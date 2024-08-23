import os
import psycopg2

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute(f"DROP TABLE IF EXISTS threads;")
cur.execute(f"DROP TABLE IF EXISTS problems;")
cur.execute(f"DROP TABLE IF EXISTS speeds;")

for stage in ("tsushima_staging", "tsushima_production"):
	cur.execute(f"CREATE SCHEMA IF NOT EXISTS {stage};")

	cur.execute(f"""
	CREATE TABLE IF NOT EXISTS {stage}.threads (
		id SERIAL PRIMARY KEY,
		sender TEXT NOT NULL UNIQUE,
		thread TEXT NOT NULL
	);
	""")

	cur.execute(f"""
	CREATE TABLE IF NOT EXISTS {stage}.problems (
		id SERIAL PRIMARY KEY,
		sender TEXT NOT NULL,
		message TEXT NOT NULL
	);
	""")

	cur.execute(f"""
	CREATE TABLE IF NOT EXISTS {stage}.speeds (
		id SERIAL PRIMARY KEY,
		sender TEXT NOT NULL UNIQUE,
		slow BOOLEAN NOT NULL
	);
	""")

conn.commit()
cur.close()
conn.close()