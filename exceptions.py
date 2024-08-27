import os

from fbmessenger.elements import Text

def process_exception(exception):
    exception = f"{exception}"
    exception = exception.replace(os.environ["A1_CHAT_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["A2_CHAT_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["B1_CHAT_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["B2_CHAT_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["C1_CHAT_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["C2_CHAT_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["A1_CONVERSION_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["A2_CONVERSION_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["B1_CONVERSION_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["B2_CONVERSION_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["C1_CONVERSION_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["C2_CONVERSION_ASSISTANT_ID"], "?")
    exception = exception.replace(os.environ["CALLBACK_URL"], "?")
    exception = exception.replace(os.environ["DATABASE_URL"], "?")
    exception = exception.replace(os.environ["FB_PAGE_TOKEN"], "?")
    exception = exception.replace(os.environ["FB_VERIFY_TOKEN"], "?")
    exception = exception.replace(os.environ["OPENAI_API_KEY"], "?")
    exception = exception.replace(os.environ["SCHEMA"], "?")
    responses = [Text(text=exception).to_dict()]
    return responses