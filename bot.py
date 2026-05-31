import asyncio
import os
import threading
import feedparser
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# =========================
# 🔐 ENV
# =========================
load_dotenv()
TOKEN = os.getenv("TOKEN")

# =========================
# 🌐 FLASK (Render Port Fix)
# =========================
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))  # ✅ RENDER FIX HIER
    app_web.run(host="0.0.0.0", port=port)

# =========================
# 🧠 STATE
# =========================
chat_ids = set()
seen = set()

# =========================
# 📡 RSS SOURCES
# =========================
RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://www.ecb.europa.eu/rss/press.html",
    "https://www.federalreserve.gov/feeds/press_all.xml"
]

# =========================
# 🔥 SCORING ENGINE
# =========================
WEIGHTS = {
    "fed": 35,
    "interest rate": 35,
    "inflation": 30,
    "recession": 40,
    "crisis": 45,
    "crash": 50,
    "bitcoin": 20,
    "crypto": 18,
    "war": 40,
    "sec": 30,
    "breaking": 20
}

def score(text: str) -> int:
    t = text.lower()
    return sum(v for k, v in WEIGHTS.items() if k in t)

# =========================
# 📡 FETCH NEWS
# =========================
def fetch_news():
    items = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)

            for e in feed.entries[:10]:
                title = getattr(e, "title", "")
                link = getattr(e, "link", "")

                if not title:
                    continue

                key = title.lower()

                if key in seen:
                    continue

                s = score(title)

                if s >= 35:
                    seen.add(key)
                    items.append((s, f"🚨 IMPACT {s}/100\n📰 {title}\n{link}"))

        except Exception as e:
            print("RSS ERROR:", e)

    return sorted(items, key=lambda x: x[0], reverse=True)

# =========================
# 🤖 TELEGRAM COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_ids.add(update.effective_chat.id)

    await update.message.reply_text(
        "🚀 NEWS ENGINE ONLINE\n🧠 High-Impact Signals Active"
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = fetch_news()

    if not data:
        await update.message.reply_text("Keine relevanten News.")
        return

    await update.message.reply_text("\n\n".join([d[1] for d in data[:5]]))

# =========================
# 🔁 BACKGROUND ENGINE
# =========================
async def engine(app):
    await asyncio.sleep(5)

    while True:
        try:
            news = fetch_news()

            if chat_ids and news:
                for chat_id in chat_ids:
                    for item in news[:3]:
                        try:
                            await app.bot.send_message(chat_id, item[1])
                        except Exception as e:
                            print("Send error:", e)

        except Exception as e:
            print("ENGINE ERROR:", e)

        await asyncio.sleep(180)

def start_engine(app):
    asyncio.create_task(engine(app))

# =========================
# 🚀 MAIN
# =========================
def main():
    # Start Flask (fix Render port issue)
    threading.Thread(target=run_web, daemon=True).start()

    # Start Telegram bot
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))

    app.post_init = start_engine

    print("🚀 BOT RUNNING (RENDER FIXED VERSION)")

    app.run_polling()

if __name__ == "__main__":
    main()