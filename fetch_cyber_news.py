import os
import re
import datetime
import requests
import feedparser
from google import genai

# 1. Fetch Environment Variables
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
RAW_TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Extract strictly the raw token pattern (numbers : alphanumeric characters)
token_match = re.search(r'\d+:[A-Za-z0-9_-]+', RAW_TELEGRAM_BOT_TOKEN)
if token_match:
    token = token_match.group(0)
else:
    token = RAW_TELEGRAM_BOT_TOKEN.strip()

# Extract strictly the chat ID (numbers, optionally starting with a minus sign for groups)
chat_id_match = re.search(r'-?\d+', TELEGRAM_CHAT_ID)
if chat_id_match:
    chat_id = chat_id_match.group(0)
else:
    chat_id = TELEGRAM_CHAT_ID.strip()
