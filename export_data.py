import pandas as pd
import sqlite3
import logging

logging.basicConfig(filename='export.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def export_all():
    conn = sqlite3.connect('contractors.db')
    df = pd.read_sql_query('SELECT * FROM contractors', conn)
    df.to_csv('contractors_export.csv', index=False)
    df.to_json('contractors_export.json', orient='records', force_ascii=False, indent=2)
    logging.info(f"Exported {len(df)} records to contractors_export.csv and contractors_export.json")
    conn.close()

if __name__ == "__main__":
    export_all() 