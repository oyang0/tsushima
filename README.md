# Tsushima
Meta App for Japanese Education through Dialogue in Messenger

https://www.facebook.com/profile.php?id=61564148264808

## How to set up

1. **Create a Facebook Page:** Log into a Facebook account, click on the "Pages" section on the left-hand side of the homepage, then click on "Create New Page", fill in the required information such as the Page name, category, and description, and then click "Create Page".

2. **Create a Facebook App:** Go to the [Facebook Developers](https://developers.facebook.com/) website and log in with a Facebook account. Click on "My Apps" in the top right corner and then "Create App". Choose "Manage Business Integrations" as the purpose of the Facebook app, then fill in the necessary details and click "Create App".

3. **Set up Messenger:** In the App's dashboard, find the "Add a Product" section and click "Set Up" in the Messenger box. In the Messenger settings, under "Access Tokens", click "Add or Remove Pages" and select the Facebook Page to be connected to the Facebook app.

4. **Get Page Access Token:** Still under "Access Tokens", click "Generate Token" for the Page just added. This will give a Page Access Token. Copy this token and save it somewhere safe. It'll be needed to add it to the Flask app's environment variables as `FB_PAGE_TOKEN`.

5. **Create an OpenAI account**: Visit the OpenAI website and sign up for an account. Provide some basic information about yourself and agree to the terms of service.

6. **Get an API key**: Once an OpenAI account has been created, access an API key from the OpenAI dashboard. This key is used to authenticate requests to the OpenAI API.

7. **Install the OpenAI Python client**: OpenAI provides a Python client library that makes it easy to interact with the API. Install it using pip with the following command.

```
pip install openai
```

8. **Set up Environment Variable**: Set the API key as an environment variable so that the Flask app can use it. In a Unix-based system, use the `export` command. In a Windows command prompt, use the `set` command.

```
export OPENAI_API_KEY=
```

```
set OPENAI_API_KEY=
```

9. **Create an Assistant**: From the OpenAI dashboard, create an Assistant and get the assistant ID.

## How to Test

1. **Install ngrok**: If ngrok hasn't been installed, download it from [ngrok](https://ngrok.com/download). After downloading, unzip the file.

2. **Install FFmpeg**: FFmpeg is a free and open-source project that produces libraries and programs for handling multimedia data. It is required by the `pydub` library for handling audio data. On Ubuntu, FFmpeg can be installed using the following command. On Windows, FFmpeg can be downloaded from its official website, extracted, and the bin folder added to the system's PATH.

```
sudo apt-get install ffmpeg
```

3. **Set up Postgres Locally**: Heroku recommends running Postgres locally to ensure parity between environments. Postgres is required by the Flask app. Follow the documentation at [Local Setup for Heroku Postgres](https://devcenter.heroku.com/articles/local-setup-heroku-postgres).

4. **Run ngrok**: Open another terminal, navigate to the directory where ngrok was unzipped, and start ngrok on the same port as the Flask app. By default, Flask runs on port 5000, so the following command would be run.

```
ngrok http 5000
```

5. **Get the ngrok URL**: ngrok will display a forwarding URL that looks something like `https://f4f6-2001-56a-78a8-a100-8d58-23db-6998-9fe3.ngrok-free.app`. This URL routes to the local Flask app.

6. **Create a Database**: A Postgre database is required by the Flask app. Create one by typing the following command.

```
createdb -h localhost -p 5432 -U 
```

7. **Create the Tables**: Create the tables required by the Flask app by typing the following command.

```
python setup.py
```

8. **Set up Environment Variables**: It is necessary to set all the environment variables that the Flask app uses (like `FB_PAGE_TOKEN`, `SYSTEM_PROMPT`, etc.). The callback URL is the ngrok URL. The Verify Token can be any string. In a Unix-based system, use the `export` command. In a Windows command prompt, use the `set` command.

```
export ASSISTANT_ID=
export CALLBACK_URL=
export DATABASE_URL=
export FB_PAGE_TOKEN=
export FB_VERIFY_TOKEN=
export SCHEMA=tsushima_staging
export SYSTEM_PROMPT=あなたは役立つアシスタントです。あなたの仕事は、書き起こされたテキストのスペルの不一致を修正することです。ピリオド、カンマ、大文字の使用など、必要な句読点のみを追加し、提供された文脈のみを使用してください。
```

```
set ASSISTANT_ID=
set CALLBACK_URL=
set DATABASE_URL=
set FB_PAGE_TOKEN=
set FB_VERIFY_TOKEN=
set SCHEMA=tsushima_staging
set SYSTEM_PROMPT=あなたは役立つアシスタントです。あなたの仕事は、書き起こされたテキストのスペルの不一致を修正することです。ピリオド、カンマ、大文字の使用など、必要な句読点のみを追加し、提供された文脈のみを使用してください。
```

9. **Run the Flask app**: Open a terminal, navigate to the directory of the Flask app, and run it by running the following command.

```
python main.py
```

10. **Set up Webhook:** In the Facebook App's dashboard, in the Messenger settings, under "Webhooks", click "Add Callback URL". Enter the ngrok URL followed by `/webhook` (e.g., `https://f4f6-2001-56a-78a8-a100-8d58-23db-6998-9fe3.ngrok-free.app/webhook`). Enter the Verify Token previously set as an environment variable. In the "Subscription Fields", select `messages` and `messaging_postbacks`, then click "Verify and Save".

11. **Subscribe App to Page:** Still under "Webhooks", select the Facebook Page connected to the app and click "Subscribe".

12. **Test the Flask app**: Navigate to the Facebook Page connected to the app, click the "Send Message" button, and type your message in the chat window that appears. If the Flask app is working, you will recieve logs from ngrok and Flask in their terminals and messages in the chat window.

## How to Deploy to Heroku

1. **Install the Heroku CLI**: Download the Heroku CLI from the Heroku website. Once installed, use the heroku command from a terminal.

2. **Log in to Heroku account**: Use the command `heroku login` and enter Heroku credentials.

3. **Create a new Heroku app**: Use the command `heroku create <app-name>`. Replace `<app-name>` with an app name.

4. **Add the FFmpeg buildpack**: The Flask app uses FFmpeg, which is not included in the standard Heroku Python buildpack. To add the FFmpeg buildpack to the Heroku app, use the following command. The `--index 1` option ensures that this buildpack is installed before any others.

```
heroku buildpacks:add --index 1 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
```

5. **Provision Heroku Postgres**: Heroku Postgres is Heroku's database as a service based on PostgreSQL. It is required by the Flask app. Follow the documentation at [Provisioning Heroku Postgres](https://devcenter.heroku.com/articles/provisioning-heroku-postgres).

6. **Push to Heroku**: Use `git push heroku main` to push the Flask app to Heroku. Heroku will detect that it's a Python app, install the necessary Python version, install dependencies from `requirements.txt`, and start the Flask app using the `Procfile`. After starting the Flask app, Heroku will give a callback URL (e.g. `https://app-name.herokuapp.com`).

7. **Set up Environment Variables**: Set environment variables on Heroku using the command `heroku config:set VARNAME=value`. Replace `VARNAME` and `value` with the names and values of the necessary variables. It is necessary to set all the environment variables that the Flask app uses (like `FB_PAGE_TOKEN`, `SYSTEM_PROMPT`, etc.). The Verify Token can be any string.

```
heroku config:set ASSISTANT_ID= CALLBACK_URL= FB_PAGE_TOKEN= FB_VERIFY_TOKEN= OPENAI_API_KEY= SCHEMA= SYSTEM_PROMPT="あなたは役立つアシスタントです。あなたの仕事は、書き起こされたテキストのスペルの不一致を修正することです。ピリオド、カンマ、大文字の使用など、必要な句読点のみを追加し、提供された文脈のみを使用してください。"
```

8. **Set up Webhook:** In the Facebook App's dashboard, in the Messenger settings, under "Webhooks", click "Add Callback URL". Enter the callback URL followed by `/webhook` (e.g., `https://app-name.herokuapp.com/webhook`). Enter the Verify Token previously set as an environment variable. In the "Subscription Fields", select `messages` and `messaging_postbacks`, then click "Verify and Save".

9. **Subscribe App to Page:** Still under "Webhooks", select the Facebook Page connected to the app and click "Subscribe".
