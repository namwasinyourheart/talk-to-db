import os
from os.path import abspath, dirname, join

# Root of the project
ROOT_DIR = abspath(join(dirname(__file__), '..'))
# Database directory and path
DB_DIR = join(ROOT_DIR, 'db')
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = join(DB_DIR, 'ecommerce.db')
# Output directory for plots
PLOTS_DIR = join(ROOT_DIR, 'output', 'plots')
os.makedirs(PLOTS_DIR, exist_ok=True)
