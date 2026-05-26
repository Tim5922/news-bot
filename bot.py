import asyncio
import os
import requests
import feedparser
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# =========================
# 🔐 LOAD ENV
# =========================
load_dotenv()
TOKEN = os.getenv("TOKEN")

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
# 🔥 IMPACT ENGINE
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
    s = 0
    for k, v in WEIGHTS.items():
        if k in t:
            s += v
    return s

# =========================
# 📡 SAFE FETCH
# =========================
def safe_fetch():
    items = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)

            if not feed or not hasattr(feed, "entries"):
                continue

            for e in feed.entries[:10]:
                title = getattr(e, "title", "")
                link = getattr(e, "link", "")

                if not title:
                    continue

                norm = title.lower()

                if norm in seen:
                    continue

                s = score(title)

                if s >= 35:
                    seen.add(norm)
                    items.append((s, f"🚨 IMPACT {s}/100\n📰 {title}\n{link}"))

        except Exception as e:
            print("RSS ERROR:", url, e)

    items.sort(key=lambda x: x[0], reverse=True)
    return items

# =========================
# 🤖 COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_ids.add(update.effective_chat.id)

    await update.message.reply_text(
        "🚀 INSTITUTIONAL NEWS ENGINE ONLINE\n"
        "🧠 High-Impact Market Signals Only\n"
        "⚡ SYSTEM ACTIVE"
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = safe_fetch()

    if not data:
        await update.message.reply_text("Keine High-Impact News aktuell.")
        return

    await update.message.reply_text("\n\n".join([d[1] for d in data[:5]]))

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧪 DEBUG SIGNAL\n\n"
        "🚨 IMPACT 90/100\n"
        "📰 TEST EVENT\n"
        "https://example.com"
    )

# =========================
# 🔁 ENGINE (24/7 LOOP)
# =========================
async def engine(app):
    await asyncio.sleep(5)

    while True:
        try:
            news = safe_fetch()

            if chat_ids and news:
                for chat_id in chat_ids:
                    for item in news[:3]:
                        await app.bot.send_message(chat_id=chat_id, text=item[1])

            await asyncio.sleep(180)

        except Exception as e:
            print("ENGINE ERROR:", e)
            await asyncio.sleep(30)

# =========================
# 🚀 START BOT
# =========================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("news", news))
app.add_handler(CommandHandler("debug", debug))

async def post_init(app):
    asyncio.create_task(engine(app))

app.post_init = post_init

print("🚀 INSTITUTIONAL ENGINE RUNNING")

app.run_polling()