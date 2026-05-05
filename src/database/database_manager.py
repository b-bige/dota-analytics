import os
import pandas as pd
import numpy as np
from sqlalchemy import text
from psycopg.types.json import Jsonb
import logging
from src.database.connection import engine

class DatabaseManager(): 
    _heroes_map: dict = None
    _items_map:  dict = None
    _npcs_map:   dict = None

    def __init__(self):
        self._initialize_mappings()
        
    def _initialize_mappings(self):
        """
        Maps the dota short names to respective IDs for handling 
        the mapping of OpenDota's data to the Database.
        """
        if DatabaseManager._heroes_map is None:
            df = self.select_to_df('SELECT id, name FROM hero_details')
            DatabaseManager._heroes_map = df.set_index('name')['id'].to_dict()
        if DatabaseManager._items_map is None:
            df = self.select_to_df('SELECT id, "shortName" FROM item_details_opendota')
            DatabaseManager._items_map = df.set_index('shortName')['id'].to_dict()
        if DatabaseManager._npcs_map is None:
            df = self.select_to_df('SELECT id, name FROM npcs')
            DatabaseManager._npcs_map = df.set_index('name')['id'].to_dict()

    def select(self, query, params: dict=None):
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return result.fetchall()
        
    def select_to_df(self, query, params: dict=None, columns=None):
        df = pd.read_sql(text(query), engine, params=params or {})
        if columns:
            df.columns = columns
        return df
    
    def execute(self, query, params: dict=None):
        with engine.begin() as conn:
            conn.execute(text(query), params or {})

    def execute_many(self, query, params: dict=None):
        with engine.begin() as conn:
            conn.execute(text(query), params or {})

    def insert_df_into_table(self, df: pd.DataFrame, table_name: str,
                          conflict_cols: list = [],
                          update_cols: list | None = None,
                          jsonb_cols: list = []) -> None:
        """
        Bulk-inserts or upserts a DataFrame into a PostgreSQL table using COPY.

        Uses a staging table pattern: data is first COPYed into a temporary
        table, then moved to the target table via INSERT ... SELECT with an
        optional ON CONFLICT clause. This avoids locking the target table
        during the COPY phase and allows atomic upsert semantics.

        Parameters
        ----------
        df : pd.DataFrame
            Data to insert. Must contain columns matching the target table.
        table_name : str
            Target PostgreSQL table name.
        conflict_cols : list, optional
            Columns forming the conflict target for upsert. If empty, plain
            INSERT is used with no conflict handling.
        update_cols : list or None, optional
            Columns to update on conflict. If None, all non-conflict columns
            are updated. Only relevant when conflict_cols is provided.
        jsonb_cols : list, optional
            Columns to serialize as JSON strings for insertion into JSONB
            columns. PostgreSQL handles the string-to-JSONB cast automatically.

        Notes
        -----
        This method uses PostgreSQL's COPY protocol rather than SQLAlchemy's
        standard df.to_sql() or executemany() for performance reasons.
        COPY is the fastest available bulk load mechanism in PostgreSQL —
        benchmarks on this codebase show ~10-20x throughput improvement over
        multi-row INSERT for large DataFrames (see scripts/benchmark_insert.py).

    
        In a context where raw throughput was less critical (smaller datasets,
        OLTP workloads), df.to_sql() or SQLAlchemy's bulk_insert_mappings()
        would be more idiomatic and portable choices.

        The staging table is named with the process ID to prevent collisions
        under concurrent execution.
        """
        if df.empty:
            logging.warning(f"Empty DataFrame passed to insert_df_into_table for '{table_name}' — skipping.")
            return

        clean_df = df.copy().astype(object) #For Driver Compatibility
        clean_df = clean_df.where(clean_df.notna(), other=None)

        for col in jsonb_cols:
            if col in clean_df.columns:
                clean_df[col] = clean_df[col].apply(
                    lambda x: Jsonb(x) if x is not None else None
                )

        col_names     = list(clean_df.columns)
        col_names_quoted = ", ".join(f'"{c}"' for c in col_names)

        upsert_clause = ""
        if conflict_cols:
            cols_to_update = update_cols or [c for c in col_names if c not in conflict_cols]
            if cols_to_update:
                update_stmt      = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in cols_to_update)
                conflict_target  = ", ".join(f'"{c}"' for c in conflict_cols)
                upsert_clause    = f"ON CONFLICT ({conflict_target}) DO UPDATE SET {update_stmt}"
            else:
                upsert_clause = f"ON CONFLICT ({', '.join(f'{c}' for c in conflict_cols)}) DO NOTHING"

        staging_table = f"staging_{table_name}_{os.getpid()}"

        try:
            with engine.connect() as sa_conn:
                raw_conn = sa_conn.connection.driver_connection
                with raw_conn.cursor() as cur:
                    try:
                        cur.execute(f'CREATE TEMP TABLE "{staging_table}" AS SELECT * FROM "{table_name}" LIMIT 0')
                        copy_query = f'COPY "{staging_table}" ({col_names_quoted}) FROM STDIN'
                        with cur.copy(copy_query) as copy:
                            for row in clean_df.itertuples(index=False, name=None):
                                copy.write_row(row)

                        cur.execute(f'''
                            INSERT INTO "{table_name}" ({col_names_quoted})
                            SELECT {col_names_quoted} FROM "{staging_table}"
                            {upsert_clause}
                        ''')

                        raw_conn.commit()

                    except Exception:
                        raw_conn.rollback()
                        raise

                    finally:
                        cur.execute(f'DROP TABLE IF EXISTS "{staging_table}"')
                        raw_conn.commit()

            mode = "Upserted" if conflict_cols else "Inserted"
            logging.info(f"{mode} {len(clean_df):,} rows into '{table_name}'.")

        except Exception as e:
            logging.error(f"Failed to insert into '{table_name}': {e}", exc_info=True)

    def _get_sa_type(self, pandas_dtype):
        from sqlalchemy import BigInteger, Float, Boolean, Text, DateTime, TIMESTAMP
        if pd.api.types.is_integer_dtype(pandas_dtype):
            return BigInteger
        elif pd.api.types.is_float_dtype(pandas_dtype):
            return Float
        elif pd.api.types.is_bool_dtype(pandas_dtype):
            return Boolean
        elif pd.api.types.is_datetime64_any_dtype(pandas_dtype):
            return TIMESTAMP
        else:
            return Text

    def get_item_id_by_name(self, name: str) -> int:
        """Returns the ID corresponding to the Item name."""
        return DatabaseManager._items_map.get(name, -1)

    def get_hero_id_by_name(self, name: str) -> int:
        """Returns the ID corresponding to the Hero name."""
        return DatabaseManager._heroes_map.get(name, -1) 
    
    def get_npc_id_by_name(self, name: str) -> int:
        """Returns the ID corresponding to the NPC name."""
        return DatabaseManager._npcs_map.get(name, -1)
    