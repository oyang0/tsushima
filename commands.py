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

    cur.execute(f"SELECT thread FROM {os.environ["SCHEMA"]}.threads WHERE sender = %s", (sender,))
    record = cur.fetchone()

    if record:
        client.beta.threads.delete(record[0])
        app.logger.debug(f"{sender} deleted from OpenAI thread: {record[0]}")

        cur.execute(f"DELETE FROM {os.environ["SCHEMA"]}.threads WHERE sender = %s", (sender,))
        conn.commit()
        app.logger.debug(f"{sender} deleted thread: {record[0]}")

    cur.close()
    conn.close()

def report_technical_problem(sender, text, app):
    message = text.removeprefix("> report technical problem ")

    if message:
        result = urlparse(os.environ["DATABASE_URL"])
        conn = psycopg2.connect(
            dbname=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname
        )
        cur = conn.cursor()
        cur.execute(f"INSERT INTO {os.environ["SCHEMA"]}.problems (sender, message) VALUES (%s, %s)", (sender, message))
        app.logger.debug(f"{sender} reported technical problem: {message}")
        conn.commit()
        cur.close()
        conn.close()

def set_voice_speed(sender, text, app):
    message = text.removeprefix("> set voice speed ")

    if message == "normal" or message == "slow":
        result = urlparse(os.environ["DATABASE_URL"])
        conn = psycopg2.connect(
            dbname=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname
        )
        cur = conn.cursor()
        cur.execute(
            f"""
            INSERT INTO {os.environ["SCHEMA"]}.speeds (sender, slow)
            VALUES (%s, %s)
            ON CONFLICT (sender)
            DO UPDATE SET slow = EXCLUDED.slow;
            """,
            (sender, message == "slow")
        )
        app.logger.debug(f"{sender} set voice speed: {message}")
        conn.commit()
        cur.close()
        conn.close()

def process_command(message, app, client):
    if message["message"]["text"].lower() == "> delete conversation":
        delete_conversation(message["sender"]["id"], app, client)
    elif message["message"]["text"].lower().startswith("> report technical problem "):
        report_technical_problem(message["sender"]["id"], message["message"]["text"].lower(), app)
    elif message["message"]["text"].lower().startswith("> set voice speed "):
        set_voice_speed(message["sender"]["id"], message["message"]["text"].lower(), app)
    