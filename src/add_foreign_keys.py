import sys
import os
sys.path.append(os.path.abspath('./src'))

from db_functions import DotaDB

## Script for adding the Foreign Key Constraint on match_id column on all tables that are
## related to a specific match. For two tables including snapshots, this was done in constraints.sql

def main():
    db = DotaDB(schema='kaggle')
    get_kaggle_reference_tables(db)
    add_foreign_keys(
        db=db, 
        tables=get_kaggle_reference_tables(db), 
        foreign_key='match_id', 
        reference_table='main_metadata', 
        primary_key='match_id', 
        cascade=True)

def get_match_tables(db: DotaDB):
    all_tables = [match_table[0] for match_table in db.query_select('SELECT table_name FROM information_schema.tables')]
    match_tables = []
    for table in all_tables:
        if table.startswith('match_') and table not in ['match_details', 'match_outpost_updates', 'match_tower_updates']:
            match_tables.append(table)
    return match_tables

def get_kaggle_reference_tables(db: DotaDB):
    tables = [match_table[0] for match_table in db.query_select(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'kaggle'"
    ) if match_table[0] != 'main_metadata' and not match_table[0].startswith('Constants_')]
    return tables

def add_foreign_keys(db: DotaDB, tables: list, foreign_key, reference_table, primary_key, cascade: bool):
    for table in tables:
        constraint_name = f'fk_{table}_{foreign_key}'
        query = f'''
            ALTER TABLE "{table}"
            ADD CONSTRAINT "{constraint_name}"
            FOREIGN KEY ("{foreign_key}")
            REFERENCES "{reference_table}" ("{primary_key}")
        '''
        if(db.query_select("""
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = %s AND table_name = %s
            """, params=(constraint_name, table))):
            continue
        if cascade:
            query = query + 'ON DELETE CASCADE'
        db.query_execute(query)

if __name__ == '__main__': 
    main()