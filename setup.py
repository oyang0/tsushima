import os
import psycopg2
import sqlite3

from main import client, messenger

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

cur.execute(f"""
CREATE TABLE IF NOT EXISTS {os.environ["SCHEMA"]}.messages (
	id SERIAL PRIMARY KEY,
	message TEXT NOT NULL UNIQUE,
    timestamp BIGINT
)
""")

conn.commit()
cur.close()
conn.close()

conn = sqlite3.connect("openai.db")
cur = conn.cursor()

cur.execute("SELECT * FROM assistants")

for row in cur.fetchall():
    if all([eval(row[6]) != assistant.metadata for assistant in client.beta.assistants.list()]):
        if row[9] in ("auto", None):
            response_format = row[9]
        else:
            response_format = eval(row[9].replace("true", "True").replace("false", "False"))

        client.beta.assistants.create(
			model=row[1],
			name=row[2],
			description=row[3],
			instructions=row[4],
			tools=eval(row[5]) if row[5] else None,
			metadata=eval(row[6]) if row[6] else None,
			temperature=row[7],
			top_p=row[8],
			response_format=response_format
		)

cur.close()
conn.close()

messenger.init_bot()