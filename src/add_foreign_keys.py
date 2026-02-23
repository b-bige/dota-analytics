import sys
import os
sys.path.append(os.path.abspath('./src'))

import db_functions as dbf

## Script for adding the Foreign Key Constraint on match_id column on all tables that are
## related to a specific match. For two tables including snapshots, this was done in constraints.sql

def main():
    db = dbf.DotaDB()
    add_foreign_keys(db, get_match_tables(db), 'match_id', 'match_details', 'id', True)

def get_match_tables(db: dbf.DotaDB):
    all_tables = [match_table[0] for match_table in db.query_select('SELECT table_name FROM information_schema.tables')]
    match_tables = []
    for table in all_tables:
        if table.startswith('match_') and table not in ['match_details', 'match_outpost_updates', 'match_tower_updates']:
            match_tables.append(table)
    return match_tables

def add_foreign_keys(db: dbf.DotaDB, tables: list, foreign_key, reference_table, primary_key, cascade: bool):
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
        print(query)
        db.query_execute(query)

if __name__ == '__main__': 
    main()