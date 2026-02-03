import pandas as pd 
import psycopg

def get_pg_type(pandas_type):
    if pd.api.types.is_integer_dtype(pandas_type):
        return "BIGINT" 
    elif pd.api.types.is_float_dtype(pandas_type):
        return "DOUBLE PRECISION"
    elif pd.api.types.is_bool_dtype(pandas_type):
        return "BOOLEAN"
    elif pd.api.types.is_datetime64_any_dtype(pandas_type):
        return "TIMESTAMP"
    else:
        return "TEXT"
    
def create_table_from_df(df, table_name, conn_str, convert_dtypes: True):
    # 1. Generate column definitions
    if convert_dtypes:
        schema_df = df.convert_dtypes()
    else:
        schema_df = df
    try:
        with psycopg.connect(conn_str) as conn:
            cols = []
            primary_key_assigned = False
            for col_name, dtype in zip(schema_df.columns, schema_df.dtypes):
                if 'id' in col_name.lower() and not primary_key_assigned:
                    pg_type = "BIGSERIAL"
                    cols.append(f'"{col_name}" {pg_type} PRIMARY KEY')
                    primary_key_assigned = True
                else:
                    pg_type = get_pg_type(dtype)
                    # Wrap column names in quotes to handle spaces or reserved words
                    cols.append(f'"{col_name}" {pg_type}')
            
            schema = ", ".join(cols)
            create_table_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({schema});'
            with conn.cursor() as cur:
                cur.execute(create_table_query)
            if primary_key_assigned:
                conn.commit()
            else:
                raise KeyError
    except Exception as e:
        print(f"Error creating table '{table_name}': {e}")
        return
    print(f"Table '{table_name}' created successfully.")

def insert_df_into_table(df, table_name, conn_str):
    clean_df = df.astype(object).where(pd.notnull(df), None)
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                col_names_str = ", ".join([f'"{c}"' for c in clean_df.columns])
                copy_query = f'COPY "{table_name}" ({col_names_str}) FROM STDIN'
                with cur.copy(copy_query) as copy:
                    for row in clean_df.itertuples(index=False):
                        copy.write_row(row)
                placeholders = ", ".join(["%s"] * len(clean_df.columns))
            conn.commit()
    except Exception as e:
        print(f"Error inserting data into table '{table_name}': {e}")
        return
    print(f"Data inserted into table '{table_name}' successfully.")