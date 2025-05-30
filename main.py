import os
import random
import requests
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import threading
import traceback
import uuid

# Load environment variables from .env
load_dotenv()

# Set API keys from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL_ID = "C08BT8X1KA5" 

# Slack client setup
client = WebClient(token=SLACK_TOKEN)

usage_stats = {"jokes_generated": 0}

# Generate a joke using OpenAI
def get_joke():
    try:
        print("💡 DEBUG: Entered get_joke()")
        print("🔑 API Key starts with:", str(openai.api_key)[:8]) # Keep this for debugging

        oai_client = openai.OpenAI() # Renamed to avoid confusion with Slack client

        # MORE VARIED PROMPTS
        themes = [
            "animals", "work", "technology", "food", "space",
            "history", "science", "puns", "dad jokes"
        ]
        adjectives = [
            "silly", "clever", "quick", "surprising", "modern", "classic"
        ]
        prompt_styles = [
            f"Tell me a short, {random.choice(adjectives)}, original joke about {random.choice(themes)}. (session: {uuid.uuid4()})",
            f"Give me a one-liner joke that's really {random.choice(adjectives)}. (ID: {uuid.uuid4()})",
            f"What's a funny, clean joke appropriate for an office? Make it about {random.choice(themes)}. (ref: {uuid.uuid4()})"
        ]
        unique_prompt = random.choice(prompt_styles)
        print(f"💬 DEBUG: Generated prompt: {unique_prompt}") # Log the prompt

        response = oai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a witty comedian who tells a wide variety of jokes."},
                {"role": "user", "content": unique_prompt}
            ],
            max_tokens=60, # Slightly more tokens just in case
            temperature=1.2, # Push temperature even higher for more randomness
            # Consider adding frequency_penalty or presence_penalty if repetition persists
            # frequency_penalty=0.5, # Value between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency.
            # presence_penalty=0.5   # Value between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far.
        )
        joke = response.choices[0].message.content.strip()
        print(f"😂 DEBUG: Received joke: {joke}") # Log the joke
        usage_stats["jokes_generated"] += 1
        return joke
    except Exception:
        print("❌ OpenAI API error occurred:")
        traceback.print_exc()
        return "Why did the backup bot get fired? It kept repeating itself."
# Post the joke to Slack
def post_joke():
    joke = get_joke()
    try:
        client.chat_postMessage(channel=CHANNEL_ID, text=f":laughing: *Joke of the Day:*\n{joke}")
        print("Joke posted successfully.")
    except SlackApiError as e:
        print(f"Error posting message to Slack: {e}")

# Flask app for serving jokes via HTTP
app = Flask(__name__)

@app.route('/')
def home():
    return "Joke of the Day bot is running!"

@app.route('/joke', methods=['POST'])
def joke_slash_command():
    response_url = request.form.get("response_url")

    def send_joke_later():
        joke = get_joke()
        requests.post(response_url, json={
            "response_type": "in_channel",
            "text": f":laughing: *Here's your joke:*\n{joke}"
        })

    threading.Thread(target=send_joke_later).start()

    # Respond immediately to Slack
    return "", 200

@app.route('/log', methods=['POST'])
def log_slash_command():
    count = usage_stats["jokes_generated"]
    return jsonify({
        "response_type": "ephemeral",
        "text": f":bar_chart: Jokes generated since last restart: {count}"
    })

@app.route('/test-joke', methods=['GET'])
def test_joke():
    joke = get_joke()
    return f"<pre>{joke}</pre>"

def run_flask():
    port = int(os.environ.get("PORT", 10000))  # Use Render-provided PORT or fallback locally
    app.run(host='0.0.0.0', port=port)

# Start the Flask server in a background thread
threading.Thread(target=run_flask).start()

# Schedule the bot to run every day at 9 AM
scheduler = BlockingScheduler()
scheduler.add_job(post_joke, 'cron', hour=9, minute=0)
print("Scheduler started. Bot will post at 9 AM daily.")
scheduler.start()