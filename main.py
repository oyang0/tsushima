import commands
import messages
import os
import retries

from flask import Flask, request, send_from_directory
from fbmessenger import BaseMessenger
from fbmessenger.attachments import Audio
from fbmessenger.elements import Text
from openai import OpenAI

def process_message(message):
    conn, cur = retries.get_connection_and_cursor_with_backoff()
    text = messages.get_text(message["message"], app, client, system_prompt)
    thread = messages.get_thread(message["sender"]["id"], cur, app, client)
    retries.message_creation_with_backoff(client, thread.id, text)
    run = retries.creation_and_polling_with_backoff(client, thread.id)
    value = messages.get_message(run, thread.id, client)
    messages.set_tts(value, message["sender"]["id"], message["message"]["mid"], cur)
    url = f"{os.environ.get("CALLBACK_URL").rstrip("/")}/audio/{message["message"]["mid"]}.mp3"
    audio = Audio(url=url, is_reusable=True)
    text = Text(text=value)
    retries.commit_with_backoff(conn)
    retries.close_cursor_and_connection_with_backoff(cur, conn)
    return (audio.to_dict(), text.to_dict())

class Messenger(BaseMessenger):
    def __init__(self, page_access_token):
        self.page_access_token = page_access_token
        super(Messenger, self).__init__(self.page_access_token)

    def message(self, message):
        app.logger.debug(f"Message received: {message}")
        self.send_action("mark_seen")

        if messages.is_audio(message["message"]) or "text" in message["message"]:
            self.send_action("typing_on")

            try:
                actions = (commands.process_command(message, client) if 
                            commands.is_command(message) else 
                            process_message(message))
            except Exception as exception:
                actions = [Text(text=f"{exception}").to_dict()]

            for action in actions:
                res = self.send(action, "RESPONSE")
                app.logger.debug(f"Message sent: {action}")
                app.logger.debug(f"Response: {res}")
        
            self.send_action("typing_off")
        
    def init_bot(self):
        app.logger.debug("Initialization started")
        self.add_whitelisted_domains("https://facebook.com/")
        res = commands.set_commands()
        app.logger.debug("Response: {}".format(res))

app = Flask(__name__)
app.debug = True
messenger = Messenger(os.environ["FB_PAGE_TOKEN"])

client = OpenAI()
system_prompt = os.environ["SYSTEM_PROMPT"]

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    app.logger.debug(f"Raw payload: {request.get_json()}")

    if request.method == "GET":
        if request.args.get("hub.verify_token") == os.environ.get("FB_VERIFY_TOKEN"):
            if request.args.get("init") and request.args.get("init") == "true":
                messenger.init_bot()
                return ""
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