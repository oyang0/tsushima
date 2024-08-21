import os
import requests
import sqlite3

from flask import Flask, request, send_from_directory
from fbmessenger import BaseMessenger
from fbmessenger.elements import Text
from openai import OpenAI
from pathlib import Path
from pydub import AudioSegment

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

    os.remove(f"{mid}.mp4")
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
    elif "text" in message:
        text = message["text"]
    return text

def get_thread(sender):
    conn = sqlite3.connect("threads.db")
    c = conn.cursor()

    c.execute(f"SELECT thread FROM threads WHERE sender = ?", (sender,))
    record = c.fetchone()

    if record:
        thread = client.beta.threads.retrieve(record[0])
    else:
        thread = client.beta.threads.create()
        c.execute("INSERT INTO threads (sender, thread) VALUES (?, ?)", (sender, thread.id))
        conn.commit()

    conn.close()

    return thread

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
    
    speech_file_path = Path(__file__).parent / f"{message["message"]["mid"]}.mp3"
    response = client.audio.speech.create(model="tts-1", voice="echo", input=message_)
    response.stream_to_file(speech_file_path)

    url = f"{os.environ.get("CALLBACK_URL")}/audio/{message["message"]["mid"]}.mp3"
    text = Text(text=message_).to_dict()

    return ({"attachment":{"type":"audio", "payload":{"url":url, "is_reusable":True}}}, text)

class Messenger(BaseMessenger):
    def __init__(self, page_access_token):
        self.page_access_token = page_access_token
        super(Messenger, self).__init__(self.page_access_token)

    def message(self, message):
        app.logger.debug(f"Message received: {message}")

        if (
            "attachments" in message["message"] and 
            message["message"]["attachments"][0]["type"] == "audio"
        ) or "text" in message["message"]:
            actions = process_message(message)
            for action in actions:
                res = self.send(action, "RESPONSE")
                if os.path.isfile(f"{message["message"]["mid"]}.mp3"):
                    os.remove(f"{message["message"]["mid"]}.mp3")
                app.logger.debug(f"Message sent: {action}")
                app.logger.debug(f"Response: {res}")

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