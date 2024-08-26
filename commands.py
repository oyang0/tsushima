from contextlib import suppress
import os
import requests
import retries

from fbmessenger.elements import Text
from openai import NotFoundError

def set_commands():
    url = f"https://graph.facebook.com/v20.0/me/messenger_profile?access_token={os.environ["FB_PAGE_TOKEN"]}"
    json = {"commands": [{"locale": "default", "commands": 
                         [{key: command[key] for key in ("name", "description")} for command in commands]}]}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=json, headers=headers)
    return response

def is_command(message):
    return ("text" in message["message"] and 
            any([command["name"] in message["message"]["text"] for command in commands]))

def set_voice_speed(message, cur, client):
    voice_speeds = {voice_speed: message["message"]["text"].find(voice_speed) for voice_speed in ("normal", "slow")}
    indices = {index: voice_speed for voice_speed, index in voice_speeds if index != -1}

    if indices:
        voice_speed = indices[min(indices)]
        retries.execution_with_backoff(
            cur, f"""
            INSERT INTO {os.environ["SCHEMA"]}.speeds (sender, slow)
            VALUES (%s, %s)
            ON CONFLICT (sender)
            DO UPDATE SET slow = EXCLUDED.slow;
            """, (message["sender"]["id"], voice_speed == "slow"))
        responses = [Text(text=f"Voice speed set to {voice_speed}").to_dict()]
    else:
        responses = [Text(text=f"Missing required argument: \"normal\" or \"slow\"").to_dict()]
    
    return responses

def delete_conversation(message, cur, client):
    retries.execution_with_backoff(
        cur, f"""
        SELECT thread
        FROM {os.environ["SCHEMA"]}.threads
        WHERE sender = %s
        """, (message["sender"]["id"],))
    record = cur.fetchone()

    if record:
        with suppress(NotFoundError):
            retries.thread_deletion_with_backoff(client, record[0])
        
        retries.execution_with_backoff(
            cur, f"""
            DELETE FROM {os.environ["SCHEMA"]}.threads
            WHERE sender = %s
            """, (message["sender"]["id"],))
    
    responses = [Text(text="Conversation deleted").to_dict()]

    return responses

def report_technical_problem(message, cur, client):
    retries.execution_with_backoff(
        cur, f"""
        INSERT INTO {os.environ["SCHEMA"]}.problems (sender, problem)
        VALUES (%s, %s)
        """, (message["sender"]["id"], message["message"]["text"]))
    responses = [Text(text="Technical problem reported").to_dict()]
    return responses

def process_command(message, client):
    conn, cur = retries.get_connection_and_cursor_with_backoff()
    indices = {message["message"]["text"].find(command["name"]): command["function"] for command in commands}
    indices.pop(-1, None)
    responses = indices[min(indices)](message, cur, client)
    retries.commit_with_backoff(conn)
    retries.close_cursor_and_connection_with_backoff(cur, conn)
    return responses

commands = [{"name": "speed",
             "description": "Set voice speed to \"normal\" or \"slow\"",
             "function": set_voice_speed},
            {"name": "delete",
             "description": "Delete this entire conversation",
             "function": delete_conversation},
            {"name": "report",
             "description": "Briefly explain what happened and how to repoduce the problem",
             "function": report_technical_problem}]