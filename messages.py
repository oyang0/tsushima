import os
import re
import requests
import retries
import sqlite3

from gtts import gTTS
from openai import NotFoundError
from pydub import AudioSegment

def is_handled(mid, cur):
    retries.execution_with_backoff(cur, f"SELECT 1 FROM {os.environ["SCHEMA"]}.messages WHERE message = %s", (mid,))
    return True if cur.fetchone() else False

def set_handled(mid, timestamp, cur):
    retries.execution_with_backoff(cur, f"""
        INSERT INTO {os.environ["SCHEMA"]}.messages (message, timestamp)
        VALUES (%s, %s)
        ON CONFLICT (message)
        DO UPDATE SET timestamp = EXCLUDED.timestamp
        """, (mid, timestamp))

def is_audio(message):
    return "attachments" in message and message["attachments"][0]["type"] == "audio"

def is_text(message):
    return "text" in message

def set_level(sender, cur):
    level = "A1"
    retries.execution_with_backoff(cur, f"""
        INSERT INTO {os.environ["SCHEMA"]}.levels (sender, level) 
        VALUES (%s, %s)
        ON CONFLICT (sender)
        DO UPDATE SET level = EXCLUDED.level
        """, (sender, level))
    return level

def get_level(sender, cur):
    retries.execution_with_backoff(cur, f"""
        SELECT level
        FROM {os.environ["SCHEMA"]}.levels
        WHERE sender = %s
        """, (sender,))
    record = cur.fetchone()
    level = record[0] if record else set_level(sender, cur)
    return level

def transcribe(url, mid, client):
    open(f"{mid}.mp4", "wb").write(requests.get(url).content)

    audio = AudioSegment.from_file(f"{mid}.mp4", "mp4")
    ten_minutes = 10 * 60 * 1000
    first_10_minutes = audio[:ten_minutes]
    first_10_minutes.export(f"{mid}.mp3", format="mp3")

    audio_file = open(f"{mid}.mp3", "rb")
    transcription = retries.transcription_creation_with_backoff(client, audio_file)
    audio_file.close()

    os.remove(f"{mid}.mp4")
    os.remove(f"{mid}.mp3")

    return transcription

def get_system_prompt(purpose):
    conn = sqlite3.connect("openai.db")
    cur = conn.cursor()
    cur.execute("SELECT prompt FROM processing WHERE purpose = ?", (purpose,))
    system_prompt = cur.fetchone()[0]
    cur.close()
    conn.close()
    return system_prompt

def get_transcription(message, client):
    transcription = transcribe(message["attachments"][0]["payload"]["url"], message["mid"], client)
    system_prompt = get_system_prompt("speech to text post-processing")
    transcription = retries.completion_creation_with_backoff(client, 0, system_prompt, transcription)
    return transcription

def convert_kanji(content, level, client):
    levels = {"A1": "kanji conversion for CEFR A1 level", "A2": "kanji conversion for CEFR A2 level",
              "B1": "kanji conversion for CEFR B1 level", "B2": "kanji conversion for CEFR B2 level",
              "C1": "kanji conversion for CEFR C1 level", "C2": "kanji conversion for CEFR C2 level"}
    system_prompt = get_system_prompt(levels[level])
    content = retries.completion_creation_with_backoff(client, 0, system_prompt, content)
    return content

def get_message(message, level, client):
    if is_audio(message):
        transcription = get_transcription(message, client)
        message = convert_kanji(transcription, level, client)
    elif is_text(message):
        message = message["text"]
    else:
        raise Exception("message is neither audio nor text")
    return message

def set_thread(sender, cur, client):
    thread = retries.thread_creation_with_backoff(client)
    retries.execution_with_backoff(cur, f"""
        INSERT INTO {os.environ["SCHEMA"]}.threads (sender, thread) 
        VALUES (%s, %s)
        ON CONFLICT (sender)
        DO UPDATE SET thread = EXCLUDED.thread
        """, (sender, thread.id))
    return thread

def get_thread(sender, cur, client):
    retries.execution_with_backoff(cur, f"""
        SELECT thread
        FROM {os.environ["SCHEMA"]}.threads
        WHERE sender = %s
        """, (sender,))
    record = cur.fetchone()

    if record:
        try:
            thread = retries.thread_retrieval_with_backoff(client, record[0])
        except NotFoundError:
            thread = set_thread(sender, cur, client)
    else:
        thread = set_thread(sender, cur, client)

    return thread

def get_assistant(level, client):
    assistants = retries.assistant_listing_with_backoff(client)
    assistant = [assistant for assistant in assistants if assistant.metadata["level"] == level][0]
    return assistant

def get_text(run, thread_id, app, client):
    if run.status == "completed": 
        messages = retries.message_listing_with_backoff(client, thread_id)
        value = eval(messages.data[0].content[0].text.value)
        app.logger.debug(f"Thoughts created: {value["thoughts"]}")
        text = value["response"]
    else:
        raise Exception(run.status)
    return text

def get_response(message, sender, level, cur, app, client):
    thread = get_thread(sender, cur, client)
    retries.message_creation_with_backoff(client, thread.id, message)
    assitant = get_assistant(level, client)
    run = retries.creation_and_polling_with_backoff(client, thread.id, assitant.id)
    response = get_text(run, thread.id, app, client)
    return response

def set_voice_speed(sender, cur):
    slow = False
    retries.execution_with_backoff(
        cur, f"""
        INSERT INTO {os.environ["SCHEMA"]}.speeds (sender, slow)
        VALUES (%s, %s)
        ON CONFLICT (sender)
        DO UPDATE SET slow = EXCLUDED.slow
        """, (sender, slow))
    return slow

def get_voice_speed(sender, cur):
    retries.execution_with_backoff(
        cur, f"""
        SELECT slow
        FROM {os.environ["SCHEMA"]}.speeds
        WHERE sender = %s
        """, (sender,))
    record = cur.fetchone()
    slow = record[0] if record else set_voice_speed(sender, cur)
    return slow

def delete_markdown_syntax(text):
    text = re.sub(r"#\s*", "", text) # headings
    text = re.sub(r"\*\s*", "", text) # bolds and italics
    text = re.sub(r">\s*", "", text) # blockquotes
    text = re.sub(r"\d+\.\s*", "", text) # ordered lists
    text = re.sub(r"-\s*", "", text) # unordered lists and horizontal rules
    text = re.sub(r"`\s*`", "", text) # codes
    text = re.sub(r"!?\[.*?\]\(.*?\)", "", text) # links and images
    text = re.sub(r"\[.*?\]|\(.*?\)|\{.*?\}", "", text) # bracketed text
    return text

def set_tts(text, message, cur):
    text = delete_markdown_syntax(text)
    tts = gTTS(text = text, lang = "ja", slow = get_voice_speed(message["sender"]["id"], cur))
    tts.save(f"{message["message"]["mid"]}.mp3")