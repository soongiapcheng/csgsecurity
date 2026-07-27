import os
import datetime
import requests
import feedparser
from google import genai

# 1. Fetch Environment Variables (Defined at top to avoid NameError)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Clean up any potential extra whitespace from environment values
token = TELEGRAM_BOT_TOKEN.strip()
chat_id = TELEGRAM_CHAT_ID.strip()

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

# Generate Telegram Content
tg_prompt = f"""
You are a cybersecurity expert. Analyze these daily news feeds:
{raw_text}

Provide a brief daily brief for Telegram.
STRICT FORMATTING RULES:
1. Do NOT use markdown symbols like ** or * for bold/italic.
2. Use ONLY raw HTML tags for formatting: <b>bold</b> for headings/emphasis, <i>italic</i> for extra detail.
3. Keep it under 3 bullets. Highlight any critical CVEs or zero-day threats if present.
"""

tg_response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents=tg_prompt,
)

# Generate Full HTML Dashboard Content
html_prompt = f"""
You are a web developer and cybersecurity analyst. 
Analyze these articles:
{raw_text}

Generate valid HTML body content for a modern daily cybersecurity dashboard.
For each article/threat:
- Wrap each item in a styled card section.
- Provide a full summary, impact assessment, and recommended mitigation steps.
- Include direct source links using target="_blank".
Return ONLY raw HTML tags (e.g. <article>, <h3>, <p>, <a>). Do not include ```html code blocks.
"""

html_response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents=html_prompt,
)

# 4. Write index.html File for GitHub Pages
today_str = datetime.datetime.now().strftime("%B %d, %Y")

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Cyber Threat Briefing - {today_str}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #0d1117;
            color: #c9d1d9;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        header {{
            border-bottom: 1px solid #30363d;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        h1 {{ color: #58a6ff; margin-bottom: 5px; }}
        .date {{ color: #8b949e; font-size: 0.9em; }}
        article {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        h3 {{ color: #f0883e; margin-top: 0; }}
        a {{ color: #58a6ff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <header>
        <h1>🔒 Daily Cybersecurity Briefing</h1>
        <div class="date">Updated: {today_str}</div>
    </header>
    <main>
        {html_response.text}
    </main>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(full_html)

# 5. Send Telegram Notification
page_url = "https://<your-username>.github.io/<your-repo>/" # Replace with your GitHub Pages URL
telegram_url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){token}/sendMessage"

telegram_msg = f"<b>🔒 Daily Cyber Briefing</b>\n\n{tg_response.text[:3000]}\n\n🔗 <a href='{page_url}'>View Full Daily Web Report</a>"

response = requests.post(
    telegram_url,
    json={
        "chat_id": chat_id,
        "text": telegram_msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
)

response.raise_for_status()
print("Briefing sent and index.html generated successfully!")
