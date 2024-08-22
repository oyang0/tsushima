import os
import psycopg2

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS threads (
	id SERIAL PRIMARY KEY,
	sender TEXT NOT NULL UNIQUE,
	thread TEXT NOT NULL
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS problems (
	id SERIAL PRIMARY KEY,
	sender TEXT NOT NULL,
	message TEXT NOT NULL
);
""")

conn.commit()
cur.close()
conn.close()