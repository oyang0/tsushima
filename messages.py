import os
import requests
import retries

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

def get_text(message, app, client, system_prompt):
    if is_audio(message):
        audio_file, mid = message["attachments"][0]["payload"]["url"], message["mid"]
        text = retries.generate_corrected_transcript(client, 0, system_prompt, transcribe, audio_file, mid, app)
        app.logger.debug(f"Transcript corrected: {text}")
    elif "text" in message:
        text = message["text"]
    else:
        raise Exception("message is neither audio nor text")
    return text

def set_thread(sender, cur, app):
    thread = retries.thread_creation_with_backoff()
    app.logger.debug(f"Thread created: {thread.id}")
    retries.execution_with_backoff(
        cur, f"""
        INSERT INTO {os.environ["SCHEMA"]}.threads (sender, thread) 
        VALUES (%s, %s)
        ON CONFLICT (sender)
        DO UPDATE SET thread = EXCLUDED.thread;
        """, (sender, thread.id))
    return thread

def get_thread(sender, cur, app):
    cur.execute(f"SELECT thread FROM {os.environ["SCHEMA"]}.threads WHERE sender = %s", (sender,))
    record = cur.fetchone()

    if record:
        try:
            thread = retries.thread_retrieval_with_backoff(record[0])
            app.logger.debug(f"Thread retrieved: {record[0]}")
        except NotFoundError:
            thread = set_thread(sender, cur, app)
    else:
        thread = set_thread(sender, cur, app)

    return thread

def get_message(run, thread_id, client):
    if run.status == "completed": 
        messages = retries.message_listing_with_backoff(client, thread_id)
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
    cur.execute(f"SELECT slow FROM {os.environ["SCHEMA"]}.speeds WHERE sender = %s", (sender,))
    record = cur.fetchone()
    slow = record[0] if record else set_voice_speed(sender, cur)
    return slow

def set_tts(text, sender, mid, cur):
    tts = gTTS(text = text, lang = "ja", slow = get_voice_speed(sender, cur))
    tts.save(f"{mid}.mp3")