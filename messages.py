import os
import requests
import retries

from contextlib import suppress
from gtts import gTTS
from openai import NotFoundError
from pydub import AudioSegment

def is_audio(message):
    return "attachments" in message and message["attachments"][0]["type"] == "audio"

def transcribe(url, mid, app, client):
    open(f"{mid}.mp4", "wb").write(requests.get(url).content)

    audio = AudioSegment.from_file(f"{mid}.mp4", "mp4")
    ten_minutes = 10 * 60 * 1000
    first_10_minutes = audio[:ten_minutes]
    first_10_minutes.export(f"{mid}.mp3", format="mp3")

    audio_file = open(f"{mid}.mp3", "rb")
    transcription = retries.transcription_creation_with_backoff(client, audio_file)
    app.logger.debug(f"Audio transcribed: {transcription}")
    audio_file.close()

    os.remove(f"{mid}.mp4")
    os.remove(f"{mid}.mp3")

    return transcription

def get_conversion_assistant(level):
    levels = {"A1": os.environ["A1_CONVERSION_ASSISTANT_ID"], "A2": os.environ["A2_CONVERSION_ASSISTANT_ID"],
              "B1": os.environ["B1_CONVERSION_ASSISTANT_ID"], "B2": os.environ["B2_CONVERSION_ASSISTANT_ID"],
              "C1": os.environ["C1_CONVERSION_ASSISTANT_ID"], "C2": os.environ["C2_CONVERSION_ASSISTANT_ID"]}
    
    if level in levels:
        assistant = levels[level]
    else:
        raise Exception("conversion assistant not found")
        
    return assistant

def convert_kanji(text, level, app, client):
    thread = retries.thread_creation_with_backoff(client)
    app.logger.debug(f"Thread created: {thread.id}")
    retries.message_creation_with_backoff(client, thread.id, text)
    app.logger.debug(f"Message created: {thread.id}")
    conversion_assistant = get_conversion_assistant(level)
    run = retries.creation_and_polling_with_backoff(client, thread.id, conversion_assistant)
    app.logger.debug(f"Message polled: {thread.id}")
    text = get_message(run, thread.id, app, client)

    with suppress(NotFoundError):
        retries.thread_deletion_with_backoff(client, thread.id)
        app.logger.debug(f"Thread deleted: {thread.id}")

    return text

def get_text(message, level, app, client):
    if is_audio(message):
        audio_file, mid = message["attachments"][0]["payload"]["url"], message["mid"]
        text = retries.generate_corrected_transcript(client, 0, transcribe, audio_file, mid, app)
        app.logger.debug(f"Transcript corrected: {text}")
        text = convert_kanji(text, level, app, client)
        app.logger.debug(f"Transcript converted: {text}")
    elif "text" in message:
        text = message["text"]
    else:
        raise Exception("message is neither audio nor text")
    return text

def set_thread(sender, cur, app, client):
    thread = retries.thread_creation_with_backoff(client)
    app.logger.debug(f"Thread created: {thread.id}")
    retries.execution_with_backoff(
        cur, f"""
        INSERT INTO {os.environ["SCHEMA"]}.threads (sender, thread) 
        VALUES (%s, %s)
        ON CONFLICT (sender)
        DO UPDATE SET thread = EXCLUDED.thread;
        """, (sender, thread.id))
    return thread

def get_thread(sender, cur, app, client):
    retries.execution_with_backoff(
        cur, f"""
        SELECT thread
        FROM {os.environ["SCHEMA"]}.threads
        WHERE sender = %s
        """, (sender,))
    record = cur.fetchone()

    if record:
        try:
            thread = retries.thread_retrieval_with_backoff(client, record[0])
            app.logger.debug(f"Thread retrieved: {record[0]}")
        except NotFoundError:
            thread = set_thread(sender, cur, app, client)
    else:
        thread = set_thread(sender, cur, app, client)

    return thread

def set_level(sender, cur):
    level = "A1"
    retries.execution_with_backoff(
        cur, f"""
        INSERT INTO {os.environ["SCHEMA"]}.levels (sender, level) 
        VALUES (%s, %s)
        ON CONFLICT (sender)
        DO UPDATE SET level = EXCLUDED.level;
        """, (sender, level))
    return level

def get_level(sender, cur):
    retries.execution_with_backoff(
        cur, f"""
        SELECT level
        FROM {os.environ["SCHEMA"]}.levels
        WHERE sender = %s
        """, (sender,))
    record = cur.fetchone()
    level = record[0] if record else set_level(sender, cur)
    return level

def get_chat_assistant(level):
    levels = {"A1": os.environ["A1_CHAT_ASSISTANT_ID"], "A2": os.environ["A2_CHAT_ASSISTANT_ID"],
              "B1": os.environ["B1_CHAT_ASSISTANT_ID"], "B2": os.environ["B2_CHAT_ASSISTANT_ID"],
              "C1": os.environ["C1_CHAT_ASSISTANT_ID"], "C2": os.environ["C2_CHAT_ASSISTANT_ID"]}
    
    if level in levels:
        assistant = levels[level]
    else:
        raise Exception("chat assistant not found")
        
    return assistant

def get_message(run, thread_id, app, client):
    if run.status == "completed": 
        messages = retries.message_listing_with_backoff(client, thread_id)
        app.logger.debug(f"Messages listed: {thread_id}")
        value = messages.data[0].content[0].text.value
    else:
        raise Exception(run.status)
    return value

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

def set_tts(text, message, cur):
    tts = gTTS(text = text, lang = "ja", slow = get_voice_speed(message["sender"]["id"], cur))
    tts.save(f"{message["message"]["mid"]}.mp3")