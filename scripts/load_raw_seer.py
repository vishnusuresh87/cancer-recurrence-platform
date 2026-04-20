"""
Load 200k sample rows from seer_data.csv into PostgreSQL using fast COPY method.
Uses psycopg2 copy_expert — 10-50x faster than to_sql with method='multi'.
"""
import io
import time
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text

CSV_PATH = '../ml-pipeline/data/processed/seer_sample_200k.csv'
DB_URL = 'postgresql://warehouse_user:warehouse_pass@localhost:5433/seer_warehouse'
NROWS = 200_000

print(f"📖 Reading {NROWS:,} rows from CSV...")
t0 = time.time()
df = pd.read_csv(CSV_PATH, nrows=NROWS)
print(f"   Done in {time.time()-t0:.1f}s — {len(df.columns)} columns loaded")

# Step 1: Create the table schema using SQLAlchemy (handles column types)
print("🏗️  Creating table schema...")
engine = create_engine(DB_URL)
with engine.begin() as conn:
    # Drop and recreate table with correct schema
    df.head(0).to_sql('raw_seer', conn, if_exists='replace', index=False)
print("   Schema created.")

# Step 2: Bulk load with PostgreSQL COPY (fastest method)
print(f"⚡ Bulk loading {len(df):,} rows via COPY...")
t1 = time.time()

conn_params = {
    'host': 'localhost',
    'port': 5433,
    'dbname': 'seer_warehouse',
    'user': 'warehouse_user',
    'password': 'warehouse_pass',
}

with psycopg2.connect(**conn_params) as pg_conn:
    with pg_conn.cursor() as cur:
        # Write DataFrame to in-memory CSV buffer
        buffer = io.StringIO()
        df.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        # Use COPY for lightning-fast insert
        cur.copy_expert(
            "COPY raw_seer FROM STDIN WITH CSV NULL ''",
            buffer
        )
    pg_conn.commit()

elapsed = time.time() - t1
print(f"✅ Loaded {len(df):,} rows to raw_seer in {elapsed:.1f}s ({len(df)/elapsed:,.0f} rows/sec)")