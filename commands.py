import os
import psycopg2

from urllib.parse import urlparse

def delete_conversation(sender, app, client):
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

    if record:
        client.beta.threads.delete(record[0])
        app.logger.debug(f"Thread deleted from OpenAI: {record[0]}")

        cur.execute(f"DELETE FROM threads WHERE sender = %s", (sender,))
        conn.commit()
        app.logger.debug(f"Thread deleted: {record[0]}")

    cur.close()
    conn.close()

def report_technical_problem(sender, text, app):
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
    app.logger.debug(f"Problem recorded: {message}")
    conn.commit()
    cur.close()
    conn.close()

def process_command(message, app, client):
    if message["message"]["text"].lower() == "> delete conversation":
        delete_conversation(message["sender"]["id"], app, client)
    elif (
        message["message"]["text"].lower().startswith("> report technical problem ") and 
        message["message"]["text"].lower() != "> report technical problem "
    ):
        report_technical_problem(message["sender"]["id"], message["message"]["text"].lower(), app)
    