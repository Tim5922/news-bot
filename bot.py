import asyncio
import os
import feedparser
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =========================
# 🔐 ENV
# =========================
TOKEN = os.environ.get("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN fehlt! Bitte in Render Environment Variables setzen.")

# =========================
# 📡 RSS SOURCES
# =========================
RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://www.ecb.europa.eu/rss/press.html",
    "https://www.federalreserve.gov/feeds/press_all.xml"
]

seen = set()
chat_ids = set()

# =========================
# 🧠 SIMPLE IMPACT FILTER
# =========================
WEIGHTS = {
    "fed": 35,
    "inflation": 30,
    "interest rate": 35,
    "recession": 40,
    "bank": 25,
    "crash": 50,
    "bitcoin": 20,
    "crypto": 18,
    "regulation": 30,
    "war": 40,
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

            for entry in feed.entries[:10]:
                title = getattr(entry, "title", "")
                link = getattr(entry, "link", "")

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
        "🚀 NEWS ENGINE ONLINE\n"
        "📡 Monitoring High Impact Events\n"
        "⚡ System Active"
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = fetch_news()

    if not data:
        await update.message.reply_text("Keine relevanten News aktuell.")
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
                        await app.bot.send_message(chat_id, item[1])

            await asyncio.sleep(180)

        except Exception as e:
            print("ENGINE ERROR:", e)
            await asyncio.sleep(30)

# =========================
# 🚀 MAIN START
# =========================
async def post_init(app):
    asyncio.create_task(engine(app))

app = Application.builder().token(TOKEN).post_init(post_init).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("news", news))

print("🚀 BOT STARTING (RENDER STABLE VERSION)")

app.run_polling()