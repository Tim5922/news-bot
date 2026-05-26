import asyncio
import os
import feedparser
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import NetworkError, TimedOut
from dotenv import load_dotenv

# =========================
# 🔐 ENV
# =========================
load_dotenv()
TOKEN = os.getenv("TOKEN")

# =========================
# LOGGING (WICHTIG FÜR RENDER)
# =========================
logging.basicConfig(level=logging.INFO)

# =========================
# 🧠 STATE
# =========================
chat_ids = set()
seen = set()

# =========================
# 📡 SOURCES
# =========================
RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://www.ecb.europa.eu/rss/press.html",
    "https://www.federalreserve.gov/feeds/press_all.xml"
]

# =========================
# 🔥 SCORING
# =========================
WEIGHTS = {
    "fed": 35,
    "interest rate": 35,
    "inflation": 30,
    "cpi": 30,
    "recession": 40,
    "bank": 25,
    "crisis": 45,
    "crash": 50,
    "bitcoin": 20,
    "ethereum": 20,
    "crypto": 18,
    "regulation": 30,
    "sec": 30,
    "war": 40,
    "liquidity": 30,
    "default": 45,
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
# 🤖 COMMANDS
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
# 🔁 STABLE ENGINE (FIXED)
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
                        except (NetworkError, TimedOut) as e:
                            print("Telegram send error:", e)
                            continue

        except Exception as e:
            print("ENGINE ERROR:", e)

        await asyncio.sleep(180)

# =========================
# 🚀 APP
# =========================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("news", news))

async def post_init(app):
    asyncio.create_task(engine(app))

app.post_init = post_init

print("🚀 BOT RUNNING STABLE VERSION")

app.run_polling()