import sys
import os
import sqlite3
import csv

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.consts import DB_DIR, DB_PATH

CSV_DIR = os.path.join(DB_DIR, "csv")  # Output to db/csv/

def export_table_to_csv(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    
    # Ensure CSV directory exists
    os.makedirs(CSV_DIR, exist_ok=True)
    
    # Save to db/csv/table_name.csv
    output_path = os.path.join(CSV_DIR, f"{table_name}.csv")
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(col_names)
        writer.writerows(rows)
    print(f"Exported {output_path}")

def main():
    conn = sqlite3.connect(DB_PATH)  # Use consts.DB_PATH
    tables = ['promotion', 'product', 'laptop', 'tablet', 'smartphone', 'category']
    for table in tables:
        export_table_to_csv(conn, table)
    conn.close()

if __name__ == '__main__':
    main()