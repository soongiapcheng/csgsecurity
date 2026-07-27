import os
import requests
import feedparser
from google import genai

# 1. Fetch Environment Variables
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# 2. Fetch Cyber Feeds
FEEDS = [
    "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    "https://feeds.feedburner.com/TheHackersNews"
]

articles = []
for url in FEEDS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:3]:
        summary_text = entry.summary[:200] if hasattr(entry, 'summary') else ''
        articles.append(f"Title: {entry.title}\nLink: {entry.link}\nSummary: {summary_text}\n")

raw_text = "\n---\n".join(articles)

# 3. Initialize Gemini Client
client = genai.Client(api_key=GEMINI_KEY)

# We explicitly instruct Gemini to use HTML tags <b> and <i> instead of Markdown asterisks
prompt = f"""
You are a cybersecurity expert. Analyze these daily news feeds:
{raw_text}

Provide a brief daily brief for Telegram.
STRICT FORMATTING RULES:
1. Do NOT use markdown symbols like ** or * for bold/italic.
2. Use ONLY raw HTML tags for formatting: <b>bold</b> for headings/emphasis, <i>italic</i> for extra detail.
3. Keep it under 3 bullets. Highlight any critical CVEs or zero-day threats if present.
"""

response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents=prompt,
)

# 4. Send Telegram Notification
page_url = "https://<your-username>.github.io/<your-repo>/" # Replace with your URL
telegram_msg = f"<b>🔒 Daily Cyber Briefing</b>\n\n{response.text[:3000]}\n\n🔗 <a href='{page_url}'>View Full Daily Web Report</a>"

requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
    json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": telegram_msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
)

print("Briefing sent successfully via Telegram!")
