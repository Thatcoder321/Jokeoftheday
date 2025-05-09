import os
import random
import requests
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Set API keys from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL_ID = "C08BT8X1KA5" 

# Slack client setup
client = WebClient(token=SLACK_TOKEN)

# Generate a joke using OpenAI
def get_joke():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # or "gpt-4" if available
            messages=[
                {"role": "system", "content": "You are a witty comedian."},
                {"role": "user", "content": "Tell me a short, funny, original joke."}
            ],
            max_tokens=50,
            temperature=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error getting joke from OpenAI: {e}")
        return "Why did the backup bot get fired? It kept repeating itself."

# Post the joke to Slack
def post_joke():
    joke = get_joke()
    try:
        client.chat_postMessage(channel=CHANNEL_ID, text=f":laughing: *Joke of the Day:*\n{joke}")
        print("Joke posted successfully.")
    except SlackApiError as e:
        print(f"Error posting message to Slack: {e}")

# Schedule the bot to run every day at 9 AM
scheduler = BlockingScheduler()
scheduler.add_job(post_joke, 'cron', hour=9, minute=0)
print("Scheduler started. Bot will post at 9 AM daily.")
scheduler.start()