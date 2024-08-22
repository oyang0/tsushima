import os
import psycopg2

from urllib.parse import urlparse

def delete_conversation(sender, client):
    result = urlparse(os.environ["DATABASE_URL"])
    conn = psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname
    )
    cur = conn.cursor()

    cur.execute(f"SELECT thread FROM threads WHERE sender = %s", (sender,))
    record = cur.fetchone()
    client.beta.threads.delete(record[0])

    cur.execute(f"DELETE FROM threads WHERE sender = %s", (sender,))
    conn.commit()

    cur.close()
    conn.close()

def report_technical_problem(sender, text):
    result = urlparse(os.environ["DATABASE_URL"])
    conn = psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname
    )
    cur = conn.cursor()
    message = text.removeprefix("> report technical problem ")
    cur.execute("INSERT INTO problems (sender, message) VALUES (%s, %s)", (sender, message))
    conn.commit()
    cur.close()
    conn.close()

def process_command(message, client):
    if message["message"]["text"].lower() == "> delete conversation":
        delete_conversation(message["sender"]["id"], client)
    elif (
        message["message"]["text"].lower().startswith("> report technical problem ") and 
        message["message"]["text"].lower() != "> report technical problem "
    ):
        report_technical_problem(message["sender"]["id"], message["message"]["text"].lower())
    