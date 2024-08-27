import os
import requests
import retries

from contextlib import suppress
from fbmessenger.elements import Text
from openai import NotFoundError

def set_commands():
    url = f"https://graph.facebook.com/v20.0/me/messenger_profile?access_token={os.environ["FB_PAGE_TOKEN"]}"
    json = {"commands": [{"locale": "default", "commands": [
        {"level": "/ set cefr level [level]"},
        {"speed": "/ set voice speed [speed]"},
        {"delete": "/ delete conversation"},
        {"report": "/ report technical problem [problem]"}]}]}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=json, headers=headers)
    return response

def is_command(message):
    return "text" in message and message["text"][0] in ("/", "@")

def delete_conversation(sender, cur, app, client):
    retries.execution_with_backoff(
        cur, f"""
        SELECT thread
        FROM {os.environ["SCHEMA"]}.threads
        WHERE sender = %s
        """, (sender,))
    record = cur.fetchone()

    if record:
        with suppress(NotFoundError):
            retries.thread_deletion_with_backoff(client, record[0])
            app.logger.debug(f"Thread deleted: {record[0]}")
        
        retries.execution_with_backoff(
            cur, f"""
            DELETE FROM {os.environ["SCHEMA"]}.threads
            WHERE sender = %s
            """, (sender,))
    
    responses = [Text(text="Conversation deleted").to_dict()]

    return responses

def report_technical_problem(command, sender, cur):
    technical_problem = command.lstrip("report technical problem").lstrip()
    retries.execution_with_backoff(
        cur, f"""
        INSERT INTO {os.environ["SCHEMA"]}.problems (sender, problem)
        VALUES (%s, %s)
        """, (sender, technical_problem))
    responses = [Text(text="Technical problem reported").to_dict()]
    return responses

def set_cefr_level(command, sender, cur):
    level = command.lstrip("set level").lstrip()
    levels = {"breakthrough": "a1", "waystage": "a2",
              "threshold": "b1", "vantage": "b2",
              "advanced": "c1", "mastery": "c2"}
    level = levels[level] if level in levels else level

    if level in ("a1", "a2", "b1", "b2", "c1", "c2"):
        retries.execution_with_backoff(
            cur, f"""
            INSERT INTO {os.environ["SCHEMA"]}.levels (sender, level) 
            VALUES (%s, %s)
            ON CONFLICT (sender)
            DO UPDATE SET level = EXCLUDED.level;
            """, (sender, level.upper()))
        responses = [Text(text=f"CEFR level set to {level.upper()}").to_dict()]
    else:
        responses = [Text(text=f"Missing required argument: 'A1', 'A2', 'B1', 'B2', 'C1', or 'C2'").to_dict()]
    
    return responses

def set_voice_speed(command, sender, cur):
    voice_speed = command.lstrip("set voice speed").lstrip()

    if voice_speed in ("normal", "slow"):
        retries.execution_with_backoff(
            cur, f"""
            INSERT INTO {os.environ["SCHEMA"]}.speeds (sender, slow)
            VALUES (%s, %s)
            ON CONFLICT (sender)
            DO UPDATE SET slow = EXCLUDED.slow;
            """, (sender, voice_speed == "slow"))
        responses = [Text(text=f"Voice speed set to {voice_speed}").to_dict()]
    else:
        responses = [Text(text=f"Missing required argument: 'normal' or 'slow'").to_dict()]
    
    return responses

def process_command(message, app, client):
    conn, cur = retries.get_connection_and_cursor_with_backoff()
    command = message["message"]["text"][1:].lower().lstrip()

    if command.startswith("delete conversation"):
        responses = delete_conversation(message["sender"]["id"], cur, app, client)
    elif command.startswith("report technical problem"):
        responses = report_technical_problem(command, message["sender"]["id"], cur)
    elif command.startswith("set cefr level"):
        responses = set_cefr_level(command, message["sender"]["id"], cur)
    elif command.startswith("set voice speed"):
        responses = set_voice_speed(command, message["sender"]["id"], cur)
    else:
        responses = [Text(text=f"Command '{command}' is not defined").to_dict()]

    retries.commit_with_backoff(conn)
    retries.close_cursor_and_connection_with_backoff(cur, conn)

    return responses