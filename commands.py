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

def delete_conversation(sender, client, cur):
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
        
        retries.execution_with_backoff(
            cur, f"""
            DELETE FROM {os.environ["SCHEMA"]}.threads
            WHERE sender = %s
            """, (sender,))
    
    response = "Conversation deleted"

    return response

def report_technical_problem(command, sender, cur):
    technical_problem = command.lstrip("report technical problem").lstrip()

    if technical_problem:
        retries.execution_with_backoff(
            cur, f"""
            INSERT INTO {os.environ["SCHEMA"]}.problems (sender, problem)
            VALUES (%s, %s)
            """, (sender, technical_problem))
        response = "Technical problem reported"
    else:
        response = "Missing required argument: [problem]"

    return response

def set_cefr_level(command, sender, cur):
    level = command.lstrip("set cefr level").lstrip()

    if level in ("a1", "a2", "b1", "b2", "c1", "c2"):
        retries.execution_with_backoff(
            cur, f"""
            INSERT INTO {os.environ["SCHEMA"]}.levels (sender, level) 
            VALUES (%s, %s)
            ON CONFLICT (sender)
            DO UPDATE SET level = EXCLUDED.level
            """, (sender, level.upper()))
        response = f"CEFR level set to {level.upper()}"
    else:
        response = "Missing required argument: 'A1', 'A2', 'B1', 'B2', 'C1', or 'C2'"
    
    return response

def set_voice_speed(command, sender, cur):
    voice_speed = command.lstrip("set voice speed").lstrip()

    if voice_speed in ("normal", "slow"):
        retries.execution_with_backoff(
            cur, f"""
            INSERT INTO {os.environ["SCHEMA"]}.speeds (sender, slow)
            VALUES (%s, %s)
            ON CONFLICT (sender)
            DO UPDATE SET slow = EXCLUDED.slow
            """, (sender, voice_speed == "slow"))

        response = f"Voice speed set to {voice_speed}"
    else:
        response = "Missing required argument: 'normal' or 'slow'"
    
    return response

def process_command(message, client, cur):
    command = message["message"]["text"][1:].lower().lstrip()

    if command.startswith("delete conversation"):
        response = delete_conversation(message["sender"]["id"], client, cur)
    elif command.startswith("report technical problem"):
        response = report_technical_problem(command, message["sender"]["id"], cur)
    elif command.startswith("set cefr level"):
        response = set_cefr_level(command, message["sender"]["id"], cur)
    elif command.startswith("set voice speed"):
        response = set_voice_speed(command, message["sender"]["id"], cur)
    else:
        response = f"Command '{command}' is not defined"

    response = Text(text=response)

    return (response.to_dict(),)