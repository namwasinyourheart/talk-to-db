import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import sqlite3
import pandas as pd
import pytest
from utils.consts import DB_PATH
import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def test_product_table_exists():
    logging.info("Running test: test_product_table_exists")
    conn = sqlite3.connect(DB_PATH)
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';")]
    conn.close()
    assert 'product' in tables, "Product table should exist in the database"

def test_first_five_products():
    logging.info("Running test: test_first_five_products")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM product LIMIT 5;", conn)
    conn.close()
    assert len(df) == 5, "Should retrieve exactly 5 products"
    assert 'name' in df.columns, "Product DataFrame should have a 'name' column"

def test_count_promotions():
    logging.info("Running test: test_count_promotions")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT COUNT(*) AS total_promotions FROM promotion;", conn)
    conn.close()
    assert df['total_promotions'].iloc[0] == 6, "There should be exactly 3 promotions in dummy data"
