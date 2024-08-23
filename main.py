import os
import psycopg2
import requests

from commands import process_command, set_voice_speed
from flask import Flask, request, send_from_directory
from fbmessenger import BaseMessenger
from fbmessenger.elements import Text
from gtts import gTTS
from openai import OpenAI, NotFoundError
from pydub import AudioSegment
from urllib.parse import urlparse

def transcribe(audio_file, mid):
    r = requests.get(audio_file, allow_redirects=True)
    open(f"{mid}.mp4", "wb").write(r.content)

    audio_file_ = AudioSegment.from_file(f"{mid}.mp4", "mp4")
    ten_minutes = 10 * 60 * 1000
    first_10_minutes = audio_file_[:ten_minutes]
    first_10_minutes.export(f"{mid}.mp3", format="mp3")

    audio_file_= open(f"{mid}.mp3", "rb")
    transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_file_, response_format="text")
    audio_file_.close()

    if os.path.isfile(f"{mid}.mp4"):
        os.remove(f"{mid}.mp4")
    if os.path.isfile(f"{mid}.mp3"):
        os.remove(f"{mid}.mp3")

    return transcription

def generate_corrected_transcript(temperature, audio_file, mid):
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=temperature,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": transcribe(audio_file, mid)
            }
        ]
    )
    return response.choices[0].message.content

def get_text(message):
    if "attachments" in message and message["attachments"][0]["type"] == "audio":
        text = generate_corrected_transcript(0, message["attachments"][0]["payload"]["url"], message["mid"])
        app.logger.debug(f"Audio processed: {text}")
    elif "text" in message:
        text = message["text"]
    return text

def create_thread(sender, conn, cur):
    thread = client.beta.threads.create()
    cur.execute(
        f"""
        INSERT INTO {os.environ["SCHEMA"]}.threads (sender, thread) 
        VALUES (%s, %s)
        ON CONFLICT (sender)
        DO UPDATE SET thread = EXCLUDED.thread;
        """, (sender, thread.id))
    conn.commit()
    app.logger.debug(f"Thread created: {thread.id}")
    return thread

def get_thread(sender):
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
        try:
            thread = client.beta.threads.retrieve(record[0])
            app.logger.debug(f"Thread retrieved: {record[0]}")
        except NotFoundError:
            thread = create_thread(sender, conn, cur)
    else:
        thread = create_thread(sender, conn, cur)

    cur.close()
    conn.close()

    return thread

def get_voice_speed(sender):
    result = urlparse(os.environ["DATABASE_URL"])
    conn = psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname
    )
    cur = conn.cursor()
    cur.execute(f"SELECT slow FROM {os.environ["SCHEMA"]}.speeds WHERE sender = %s", (sender,))
    record = cur.fetchone()

    if record:
        slow = record[0]
    else:
        slow = False
        set_voice_speed(sender, "normal", app)

    cur.close()
    conn.close()

    return slow

def process_message(message):
    text = get_text(message["message"])

    thread = get_thread(message["sender"]["id"])
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=text)
    run = client.beta.threads.runs.create_and_poll(thread_id=thread.id, assistant_id=os.environ["ASSISTANT_ID"])

    while run.status == "in_progress":
        pass

    if run.status == "completed": 
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        message_ = messages.data[0].content[0].text.value
    else:
        message_ = run.status

    speech = gTTS(text = message_, lang = "ja", slow = get_voice_speed(message["sender"]["id"]))
    speech.save(f"{message["message"]["mid"]}.mp3")

    url = f"{os.environ.get("CALLBACK_URL")}/audio/{message["message"]["mid"]}.mp3"
    text = Text(text=message_).to_dict()

    return ({"attachment":{"type":"audio", "payload":{"url":url, "is_reusable":True}}}, text)

class Messenger(BaseMessenger):
    def __init__(self, page_access_token):
        self.page_access_token = page_access_token
        super(Messenger, self).__init__(self.page_access_token)

    def message(self, message):
        app.logger.debug(f"Message received: {message}")

        if "text" in message["message"] and message["message"]["text"][0] == ">":
            self.send_action("typing_on")
            process_command(message, app, client)
            self.send_action("typing_off")
        elif (
            "attachments" in message["message"] and 
            message["message"]["attachments"][0]["type"] == "audio"
        ) or "text" in message["message"]:
            self.send_action("typing_on")
            actions = process_message(message)
            for action in actions:
                res = self.send(action, "RESPONSE")
                if os.path.isfile(f"{message["message"]["mid"]}.mp3"):
                    os.remove(f"{message["message"]["mid"]}.mp3")
                app.logger.debug(f"Message sent: {action}")
                app.logger.debug(f"Response: {res}")
            self.send_action("typing_off")

app = Flask(__name__)
app.debug = True
messenger = Messenger(os.environ["FB_PAGE_TOKEN"])

client = OpenAI()
system_prompt = os.environ["SYSTEM_PROMPT"]

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == os.environ.get("FB_VERIFY_TOKEN"):
            return request.args.get("hub.challenge")
        raise ValueError("FB_VERIFY_TOKEN does not match.")
    elif request.method == "POST":
        messenger.handle(request.get_json(force=True))
    return ""

@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(".", filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0")