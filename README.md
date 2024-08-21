# Tsushima
Meta App for Japanese Dialogue Education in Messenger

## How to Deploy to Heroku

1. **Install the Heroku CLI**: Download the Heroku CLI from the Heroku website. Once installed, use the heroku command from a command shell.

2. **Log in to Heroku account**: Use the command `heroku login` and enter Heroku credentials.

3. **Create a new Heroku app**: Use the command `heroku create <app-name>`. Replace `<app-name>` with an app name.

4. **Push to Heroku**: Use `git push heroku main` to push the Flask app to Heroku. Heroku will detect that it's a Python app, install the necessary Python version, install dependencies from `requirements.txt`, and start the Flask app using the `Procfile`. After starting the Flask app, Heroku will give a callback URL (e.g. `https://app-name.herokuapp.com`).

5. **Set up environment variables**: Set environment variables on Heroku using the command `heroku config:set VARNAME=value`. Replace `VARNAME` and `value` with the names and values of the necessary variables. It is necessary to set all the environment variables that the Flask app uses (like `FB_PAGE_TOKEN`, `SYSTEM_PROMPT`, etc.).

```
heroku config:set ASSISTANT_ID= CALLBACK_URL= FB_PAGE_TOKEN= FB_VERIFY_TOKEN= OPENAI_API_KEY= SYSTEM_PROMPT="You are a helpful assistant. Your task is to correct any spelling discrepancies in the transcribed text. Only add necessary punctuation such as periods, commas, and capitalization, and use only the context provided."
```
