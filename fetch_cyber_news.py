# 5. Send Telegram Notification
page_url = "https://<your-username>.github.io/<your-repo>/" # Replace with your GitHub Pages URL

# Ensure TELEGRAM_BOT_TOKEN has no extra whitespace
token = TELEGRAM_BOT_TOKEN.strip()
telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"

telegram_msg = f"<b>🔒 Daily Cyber Briefing</b>\n\n{tg_response.text[:3000]}\n\n🔗 <a href='{page_url}'>View Full Daily Web Report</a>"

# Make the post request with a clean URL string
response = requests.post(
    telegram_url,
    json={
        "chat_id": TELEGRAM_CHAT_ID.strip(),
        "text": telegram_msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
)

response.raise_for_status()
print("Briefing sent and index.html generated successfully!")
