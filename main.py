import logging
import json
import asyncio
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    ContextTypes,
)
from aiohttp import web
import os
import sys

# 🔧 Bot token and channel ID from env
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
RENDER_EXTERNAL_URL = "https://jigarbot.onrender.com"
WEBHOOK_PATH = "/telegram"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}" if RENDER_EXTERNAL_URL else ""

app = None  # Global Application instance for webhook processing

# JSON files to track users
USER_FILE = "joined_users.json"
LEFT_FILE = "left_users.json"

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Your existing functions below (unchanged) ---
def load_json_file(filename):
    try:
        with open(filename, "r") as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json_file(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)

def init_file(filename, default_data):
    try:
        with open(filename, "x") as f:
            json.dump(default_data, f)
    except FileExistsError:
        pass

def save_user(user_id: int):
    init_file(USER_FILE, [])
    try:
        with open(USER_FILE, "r") as f:
            users = json.load(f)
    except json.JSONDecodeError:
        users = []

    if user_id not in users:
        users.append(user_id)
        with open(USER_FILE, "w") as f:
            json.dump(users, f)
        logger.info(f"Saved user ID: {user_id}")

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat

    try:
        await context.bot.approve_chat_join_request(chat.id, user.id)
        logger.info(f"Approved join request from {user.id} ({user.full_name})")
    except Exception as e:
        logger.error(f"Failed to approve join request: {e}")
        return

    save_user(user.id)

    left_users = load_json_file(LEFT_FILE)
    if str(user.id) in left_users:
        del left_users[str(user.id)]
        save_json_file(LEFT_FILE, left_users)
        logger.info(f"User {user.id} rejoined, removed from left_users")

    welcome_text = f"""
👋 Hi {user.first_name}!

📊 TRADE WITH JIGAR 📊

Traders with big losses are now recovering fast and hitting daily profit goals after joining our VIP group 💰

I use AI Signal Software to give sure-shot trades directly in the VIP group 👑

1⃣ Register now 👇

https://market-qx.pro/sign-up/?lid=1413340

2⃣ Deposit 30$ or above 💵

3⃣ Send Trader ID – @JIGAR0648 ✅

🔥 Join us | Recover fast | Earn daily 🔥

"""

    keyboard = [
        [InlineKeyboardButton("👨‍💼 Admin", url="https://t.me/Jigar0648?text=I%20want%20to%20Join%20VIP")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=welcome_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        logger.info(f"Sent welcome message to {user.full_name}")
    except Exception as e:
        logger.warning(f"Couldn't send DM to {user.full_name}: {e}")

async def check_who_left(context: ContextTypes.DEFAULT_TYPE):
    init_file(USER_FILE, [])
    init_file(LEFT_FILE, {})

    try:
        with open(USER_FILE, "r") as f:
            user_ids = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_ids = []

    left_users = load_json_file(LEFT_FILE)
    current_time = time.time()

    for user_id in user_ids:
        try:
            member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
            if member.status in ["left", "kicked"]:
                user_key = str(user_id)
                user_data = left_users.get(user_key, {"count": 0, "first_sent_at": None, "last_sent_at": None})

                if user_data["count"] >= 30:
                    continue

                send_now = False

                if user_data["first_sent_at"] is None:
                    if user_data["last_sent_at"] is None:
                        if user_key not in left_users:
                            user_data["first_sent_at"] = current_time
                        if current_time - user_data["first_sent_at"] >= 60:
                            send_now = True
                elif user_data["last_sent_at"] is None:
                    if current_time - user_data["first_sent_at"] >= 60:
                        send_now = True
                else:
                    if current_time - user_data["last_sent_at"] >= 86400:
                        send_now = True

                if send_now:
                    try:
                        user_obj = await context.bot.get_chat(user_id)
                        first_name = user_obj.first_name if user_obj else "there"

                        farewell_text = (
                            f"📈 Hey {first_name}!  YOU JUST LEFT “ TRADE WITH JIGAR ”  \n\n"
                            "Maybe it’s not the right time now — no worries 🤝\n\n"
                            "But remember , our VIP members are making daily profit and recovering losses using AI software - based signals 📊\n\n"
                            "( Whenever you're ready to start again )\n\n"
                            "🔁 To join back , click on ✅ Join Channel Now button\n\n"
                            "🔹 Need help or have any questions ? \n\n"
                            "🔹 Message me : @JIGAR0648 ✅"
                        )

                        keyboard = InlineKeyboardMarkup(
                            [[
                                InlineKeyboardButton("✅ Join Channel Now", url="https://t.me/+_feJE83TCNJlZmFl")
                            ]]
                        )

                        await context.bot.send_message(
                            chat_id=user_id,
                            text=farewell_text,
                            reply_markup=keyboard
                        )

                        user_data["count"] += 1
                        user_data["last_sent_at"] = current_time
                        user_data["first_sent_at"] = user_data.get("first_sent_at", current_time)
                        logger.info(f"Sent farewell #{user_data['count']} to user {user_id}")
                    except Exception as e:
                        logger.warning(f"Could not send farewell to {user_id}: {e}")

                left_users[user_key] = user_data

            else:
                if str(user_id) in left_users:
                    del left_users[str(user_id)]
                    logger.info(f"Removed {user_id} from left_users (rejoined).")

        except Exception as e:
            logger.error(f"Error checking user {user_id}: {e}")

    save_json_file(LEFT_FILE, left_users)

# --- End of your unchanged functions ---

# --- New webhook-related aiohttp code and main ---

# Health check endpoint for Render or uptime
async def handle_health(request):
    return web.Response(text="Bot is alive and running! 🚀")

# Webhook POST endpoint
async def handle_webhook(request):
    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
    except Exception as e:
        logger.error(f"Failed to process update: {e}")
    return web.Response(text="OK")

async def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app = web.Application()
    web_app.router.add_get('/', handle_health)
    web_app.router.add_post(WEBHOOK_PATH, handle_webhook)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"HTTP server running on port {port}")

# Keep-alive ping for Render or uptime services
async def keep_alive_ping(url: str, interval: int = 30):
    import aiohttp
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    logger.info(f"[PING] Keep-alive ping to {url} — Status: {resp.status}")
        except Exception as e:
            logger.warning(f"[PING ERROR] {e}")
        await asyncio.sleep(interval)

async def main():
    global app
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add your existing handlers unchanged
    app.add_handler(ChatJoinRequestHandler(handle_join_request))

    # Add your job to check who left every 60 seconds
    app.job_queue.run_repeating(check_who_left, interval=60, first=10)

    # Initialize and start bot
    await app.initialize()
    await app.bot.set_webhook(WEBHOOK_URL)
    await app.start()

    # Start aiohttp web server
    await run_web_server()

    # Start keep-alive pinger if URL provided
    if RENDER_EXTERNAL_URL:
        asyncio.create_task(keep_alive_ping(RENDER_EXTERNAL_URL))

    # Keep running
    stop_event = asyncio.Event()
    await stop_event.wait()

    # On shutdown
    await app.stop()
    await app.shutdown()

if __name__ == "__main__":
    if sys.platform.startswith('win') and sys.version_info[:2] >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
