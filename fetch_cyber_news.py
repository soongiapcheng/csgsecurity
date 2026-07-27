import os
import requests
import feedparser
import google.generativeai as genai

# Config
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# 1. Fetch Feeds
FEEDS = [
    "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    "https://feeds.feedburner.com/TheHackersNews"
]

articles = []
for url in FEEDS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:3]:
        articles.append(f"Title: {entry.title}\nLink: {entry.link}\nSummary: {entry.summary[:200]}\n")

raw_text = "\n---\n".join(articles)

# 2. Summarize with Gemini AI
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-3.5-flash')

prompt = f"""
You are a cybersecurity expert. Analyze these daily news feeds:
{raw_text}

Provide:
1. A brief 3-bullet summary for a Telegram alert.
2. An HTML section for a web dashboard detailing each threat.
"""

response = model.generate_content(prompt)

# 3. Send Telegram Notification
page_url = "https://<your-username>.github.io/<your-repo>/" # Or Cloudflare Pages URL
telegram_msg = f"<b>🔒 Daily Cyber Briefing</b>\n\n{response.text[:3000]}\n\n🔗 <a href='{page_url}'>View Full Daily Web Report</a>"

requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
    json={"chat_id": TELEGRAM_CHAT_ID, "text": telegram_msg, "parse_mode": "HTML"}
)
