import os
import psycopg2

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

for stage in ("tsushima_staging", "tsushima_production"):
	cur.execute("CREATE SCHEMA IF NOT EXISTS %s;", (stage,))

	cur.execute("""
	CREATE TABLE IF NOT EXISTS %s.threads (
		id SERIAL PRIMARY KEY,
		sender TEXT NOT NULL UNIQUE,
		thread TEXT NOT NULL
	);
	""", (stage,))

	cur.execute("""
	CREATE TABLE IF NOT EXISTS %s.problems (
		id SERIAL PRIMARY KEY,
		sender TEXT NOT NULL,
		message TEXT NOT NULL
	);
	""", (stage,))

	cur.execute("""
	CREATE TABLE IF NOT EXISTS %s.speeds (
		id SERIAL PRIMARY KEY,
		sender TEXT NOT NULL UNIQUE,
		slow BOOLEAN NOT NULL
	);
	""", (stage,))

conn.commit()
cur.close()
conn.close()