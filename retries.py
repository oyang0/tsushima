import os
import psycopg2

from openai import NotFoundError
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_not_exception_type, RetryError

system_prompt = "あなたは役立つアシスタントです。あなたの仕事は、書き起こされたテキストのスペルの不一致を修正することです。ピリオド、カンマ、大文字の使用など、必要な句読点のみを追加し、提供された文脈のみを使用してください。"

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def connection_with_backoff():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    return conn

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def get_cursor_with_backoff(conn):
    cur = conn.cursor()
    return cur

def get_connection_and_cursor_with_backoff():
    conn = connection_with_backoff()
    cur = get_cursor_with_backoff(conn)
    return conn, cur

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def commit_with_backoff(conn):
    conn.commit()

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def close_cursor_with_backoff(cur):
    cur.close()

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def close_connection_with_backoff(conn):
    conn.close()

def close_cursor_and_connection_with_backoff(cur, conn):
    close_connection_with_backoff(cur)
    close_connection_with_backoff(conn)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def execution_with_backoff(cur, query, vars = None):
    cur.execute(query, vars)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def transcription_creation_with_backoff(client, audio_file):
    transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_file, response_format="text", prompt="中村由美, 中村, 由美")
    return transcription

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def thread_creation_with_backoff(client):
    thread = client.beta.threads.create()
    return thread

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6), retry=retry_if_not_exception_type(NotFoundError), reraise=True)
def thread_retrieval_with_backoff(client, thread_id):
    thread = client.beta.threads.retrieve(thread_id)
    return thread

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6), retry=retry_if_not_exception_type(NotFoundError), reraise=True)
def thread_deletion_with_backoff(client, thread_id):
    client.beta.threads.delete(thread_id)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def message_creation_with_backoff(client, thread_id, content):
    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=content)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def message_listing_with_backoff(client, thread_id):
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return messages

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def generate_corrected_transcript(client, temperature, transcribe, audio_file, mid, app):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=temperature,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": transcribe(audio_file, mid, app, client)
            }
        ]
    )
    return response.choices[0].message.content

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def creation_and_polling_with_backoff(client, thread_id, assistant_id):
    run = client.beta.threads.runs.create_and_poll(thread_id=thread_id, assistant_id=assistant_id)

    while run.status == "in_progress":
        pass

    if run.status == "failed":
        raise RetryError(run.last_error.message)
    elif run.status == "incomplete":
        raise RetryError(run.incomplete_details.reason)
    
    return run