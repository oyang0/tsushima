import os
import psycopg2

from main import messenger

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

cur.execute(f"CREATE SCHEMA IF NOT EXISTS {os.environ["SCHEMA"]}")

cur.execute(f"""
CREATE TABLE IF NOT EXISTS {os.environ["SCHEMA"]}.threads (
	id SERIAL PRIMARY KEY,
	sender TEXT NOT NULL UNIQUE,
	thread TEXT NOT NULL
)
""")

cur.execute(f"""
CREATE TABLE IF NOT EXISTS {os.environ["SCHEMA"]}.levels (
	id SERIAL PRIMARY KEY,
	sender TEXT NOT NULL UNIQUE,
	level TEXT NOT NULL
)
""")

cur.execute(f"""
CREATE TABLE IF NOT EXISTS {os.environ["SCHEMA"]}.speeds (
	id SERIAL PRIMARY KEY,
	sender TEXT NOT NULL UNIQUE,
	slow BOOLEAN NOT NULL
)
""")

cur.execute(f"""
CREATE TABLE IF NOT EXISTS {os.environ["SCHEMA"]}.problems (
	id SERIAL PRIMARY KEY,
	sender TEXT NOT NULL,
	problem TEXT NOT NULL
)
""")

conn.commit()
cur.close()
conn.close()

messenger.init_bot()