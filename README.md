# Tsushima
Facebook Messenger App for Japanese Education through Dialogue

https://www.facebook.com/profile.php?id=61564148264808

## How to set up

1. **Create a Facebook Page:** Go to [Facebook](https://www.facebook.com/). Click on the menu icon (three horizontal lines) in the top-right corner. Select "Pages" from the menu. Click on "Create New Page." Enter a Page name, category, and description. Click "Create Page."

2. **Set Up Page Details:** Add a profile picture and cover photo. Fill in additional details like contact information, location, and hours of operation. Click "Save."

3. **Create a Facebook Developer Account:** Go to [Facebook for Developers](https://developers.facebook.com/). Click "Get Started" and follow the prompts to create a developer account.

4. **Create a New App:** In the Facebook for Developers dashboard, click "My Apps" in the top-right corner. Click "Create App." Select "Manage Business Integrations" and click "Continue." Enter a App Display Name, Contact Email, and click "Create App ID."

5. **Add Messenger Product:** In the app dashboard, click "Add a Product" in the left-hand menu. Find "Messenger" and click "Set Up."

6. **Generate a Page Access Token:** In the Messenger settings, scroll down to "Access Tokens." Select the Facebook Page created earlier. Click "Generate Token" and copy the token.

7. **Integrate OpenAI API:** Sign up for an OpenAI account at [OpenAI](https://www.openai.com/). Obtain an API key from the OpenAI dashboard.

## How to Test

1. **Install Required Software:** Ensure Python is installed. Download and install ngrok from [ngrok's official website](https://ngrok.com/). Download and install FFmpeg from [FFmpeg's official website](https://ffmpeg.org/download.html). Download and install PostgreSQL from [PostgreSQL's official website](https://www.postgresql.org/download/).

2. **Set Up Postgres Database:** Start the PostgreSQL service. Create a new database and user for the app.

```sh
psql -U postgres
CREATE DATABASE tsushima
CREATE USER user WITH ENCRYPTED PASSWORD 'password'
GRANT ALL PRIVILEGES ON DATABASE tsushima TO user
```

3. **Set Up Environment Variables:** Add the following environment variables:

```
set DATABASE_URL=postgresql://user:password@localhost/tsushima
set FB_PAGE_TOKEN=fb_page_token
set FB_VERIFY_TOKEN=fb_verify_token
set OPENAI_API_KEY=openai_api_key
set SCHEMA=schema
```

4. **Install Python Dependencies:** Add necessary dependencies (e.g., `flask`, `psycopg2`, `requests`). Install dependencies using pip:

```sh
pip install -r requirements.txt
```

5. **Run Ngrok:** Start ngrok to expose the local server to the internet. Note the HTTPS URL provided by ngrok (e.g., `https://ngrok-url.ngrok-free.app`).

```sh
ngrok http 5000
```

6. **Set Up CALLBACK_URL:** Set the `CALLBACK_URL` in the environent variables with the ngrok URL.

```
set CALLBACK_URL=https://ngrok-url.ngrok-free.app
```

7. **Run the App Server:** Start the Flask server.

```sh
python setup.py
python main.py
```

8. **Set Up Facebook Messenger Webhook:** Go to the Facebook Developer Portal. Select the app and navigate to the Messenger settings. Under "Webhooks", click "Add Callback URL". Enter the ngrok URL followed by the webhook endpoint (e.g., `https://ngrok-url.ngrok-free.app/webhook`). Enter the `FB_VERIFY_TOKEN` set in the environment variables. Subscribe to the necessary events (e.g., messages, messaging_postbacks).

9. **Test the App:** Send a message to the Facebook page. Check the server logs to ensure the webhook is receiving and processing the messages correctly.

## How to Deploy to Heroku

1. **Create a Heroku Account:** Sign up for a free account at [Heroku](https://www.heroku.com/).

2. **Install Heroku CLI:** Download and install the Heroku CLI from [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).

3. **Log in to Heroku:** Open a terminal and log in to Heroku:

```sh
heroku login
```

4. **Create a New Heroku App:** Navigate to the project directory and create a new Heroku app:

```sh
heroku create app-name
```

5. **Add FFmpeg Buildpack:** Add the FFmpeg buildpack to the Heroku app:

```sh
heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
```

6. **Set Up Postgres:** Add the Heroku Postgres add-on to the app:

```sh
heroku addons:create heroku-postgresql:hobby-dev
```

7. **Set Environment Variables:** Set the necessary environment variables for the app:

```sh
heroku config:set FB_PAGE_TOKEN=fb_page_token
heroku config:set FB_VERIFY_TOKEN=fb_verify_token
heroku config:set OPENAI_API_KEY=openai_api_key
heroku config:set SCHEMA=schema
```

8. **Deploy the Code:** Initialize a git repository if not already done, then push the code to Heroku:
```sh
git init
git add .
git commit -m "Initial commit"
git push heroku master
```

9. **Set Up CALLBACK_URL:** Set the `CALLBACK_URL` in the environent variables with the URL given by Heroku.

```
heroku config:set CALLBACK_URL=https://heroku-url.herokuapp.com
```

10. **Set Up Webhook on Facebook Developer Portal:** Go to the Facebook Developer Portal and set up a webhook with the `CALLBACK_URL` and `FB_VERIFY_TOKEN`.

11. **Monitor Logs:** Monitor app logs to debug any issues:

```sh
heroku logs --tail
```