import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.consts import DB_DIR, DB_PATH
import sqlite3
import pandas as pd

CSV_DIR = os.path.join(DB_DIR, "csv")

def create_tables(conn):
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS category (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS promotion (
            id INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            discount REAL NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            promotion_id INTEGER,
            category_id INTEGER,
            FOREIGN KEY(promotion_id) REFERENCES promotion(id),
            FOREIGN KEY(category_id) REFERENCES category(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS laptop (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            ram INTEGER NOT NULL,
            storage INTEGER NOT NULL,
            processor TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES product(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS tablet (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            screen_size REAL NOT NULL,
            battery INTEGER NOT NULL,
            support_sim INTEGER NOT NULL,
            FOREIGN KEY(product_id) REFERENCES product(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS smartphone (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            camera_megapixels REAL NOT NULL,
            os TEXT NOT NULL,
            battery INTEGER NOT NULL,
            FOREIGN KEY(product_id) REFERENCES product(id)
        )
    ''')

    conn.commit()

def insert_data_from_csv(conn):
    tables = [
        'category',
        'promotion',
        'product',
        'laptop',
        'tablet',
        'smartphone'
    ]

    for table in tables:
        csv_path = os.path.join(CSV_DIR, f"{table}.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found for {table} at {csv_path}")

        df = pd.read_csv(csv_path)
        data = [tuple(row) for row in df.values]
        columns = ', '.join(df.columns)
        placeholders = ', '.join(['?'] * len(df.columns))

        conn.executemany(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            data
        )

    conn.commit()

def main():
    # remove existing database to start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    insert_data_from_csv(conn)
    conn.close()
    print(f'Database created at {DB_PATH} using CSV data from {CSV_DIR}')

if __name__ == '__main__':
    main()
