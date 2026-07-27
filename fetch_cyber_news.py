import os
import re
import time
import datetime
import requests
import feedparser
from google import genai

# ==========================================
# 1. FETCH & SANITIZE ENVIRONMENT VARIABLES
# ==========================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
RAW_TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
RAW_TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Extract strictly the token pattern (e.g., 123456789:ABCdefGHIjklMNO) 
# even if the secret accidentally contains Markdown links or extra URLs
token_candidates = re.findall(r'\d+:[A-Za-z0-9_-]+', RAW_TELEGRAM_BOT_TOKEN)
if token_candidates:
    token = token_candidates[-1]
else:
    token = re.sub(r'[\[\]\(\)\'\"]', '', RAW_TELEGRAM_BOT_TOKEN).strip()

# Extract strictly numbers for chat ID (handles negative numbers for group/channel IDs)
chat_id_candidates = re.findall(r'-?\d+', RAW_TELEGRAM_CHAT_ID)
if chat_id_candidates:
    chat_id = chat_id_candidates[-1]
else:
    chat_id = re.sub(r'[\[\]\(\)\'\"]', '', RAW_TELEGRAM_CHAT_ID).strip()

print(f"Sanitized Bot Token length: {len(token)} characters")

# ==========================================
# 2. FETCH CYBERSECURITY RSS FEEDS
# ==========================================
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

# ==========================================
# 3. GENERATE BRIEFINGS VIA GEMINI AI (WITH RETRY)
# ==========================================
client = genai.Client(api_key=GEMINI_KEY)

def generate_with_retry(model, contents, max_retries=3):
    """Retries Gemini API call in case of transient 503 capacity spikes."""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=model, contents=contents)
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print(f"Server busy (503). Retrying in {(attempt + 1) * 5} seconds...")
                time.sleep((attempt + 1) * 5)
            else:
                raise e
    return client.models.generate_content(model=model, contents=contents)

# A. Generate Telegram Content (HTML formatted)
tg_prompt = f"""
You are a cybersecurity expert. Analyze these daily news feeds:
{raw_text}

Provide a brief daily brief for Telegram.
STRICT FORMATTING RULES:
1. Do NOT use markdown symbols like ** or * for bold/italic.
2. Use ONLY raw HTML tags for formatting: <b>bold</b> for headings/emphasis, <i>italic</i> for extra detail.
3. Keep it under 3 bullets. Highlight any critical CVEs or zero-day threats if present.
"""

tg_response = generate_with_retry('gemini-2.5-flash', tg_prompt)

# B. Generate Web Dashboard Body Content
html_prompt = f"""
You are a web developer and cybersecurity analyst. 
Analyze these articles:
{raw_text}

Generate valid HTML body content for a modern daily cybersecurity dashboard.
For each article/threat:
- Wrap each item in an <article> styled card section.
- Provide a full summary, impact assessment, and recommended mitigation steps.
- Include direct source links using target="_blank".
Return ONLY raw HTML tags (e.g. <article>, <h3>, <p>, <a>). Do not include ```html code blocks.
"""

html_response = generate_with_retry('gemini-2.5-flash', html_prompt)

# ==========================================
# 4. GENERATE AND SAVE index.html
# ==========================================
today_str = datetime.datetime.now().strftime("%B %d, %Y")
html_body = html_response.text if html_response.text else "<p>No threat updates generated for today.</p>"

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
        {html_body}
    </main>
</body>
</html>
"""

# Force writing to workspace root
file_path = os.path.join(os.getcwd(), "index.html")
with open(file_path, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"File successfully written to: {file_path}")

# ==========================================
# 5. SEND TELEGRAM NOTIFICATION
# ==========================================
page_url = "[https://soongiapcheng.github.io/csgsecurity/](https://soongiapcheng.github.io/csgsecurity/)"
telegram_url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){token}/sendMessage"

telegram_msg = f"<b>🔒 Daily Cyber Briefing</b>\n\n{tg_response.text[:3000]}\n\n🔗 <a href='{page_url}'>View Full Daily Web Report</a>"

try:
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
except Exception as err:
    print(f"Warning: Telegram notification failed, but index.html was generated. Error: {err}")
