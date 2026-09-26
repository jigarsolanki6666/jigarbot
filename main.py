import logging
import json
import asyncio
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    ContextTypes,
    CommandHandler,
)
from aiohttp import web
import os
import sys
from types import SimpleNamespace
from contextlib import suppress

# 🔧 Bot token and channel ID from envs
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://jigarbot-1.onrender.com").rstrip("/")
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

async def send_welcome_message(context, user, chat_id):
    welcome_text = f"""
👋 Hi {user.first_name}!

📊 TRADE WITH JIGAR 📊

Many traders who were struggling are now recovering losses and achieving consistent daily profits with our VIP guidance 💰 

◾️Main Channel : https://t.me/+_feJE83TCNJlZmFl

◾️ How to Join VIP 👇

1️⃣ Register : https://broker-qx.pro/sign-up/?lid=1413340

2️⃣ Deposit $30 or more 💵

3️⃣ Send your Trader ID to @JIGAR0648 ✅

Your next profitable trade could be just one step away. Join today and trade with confidence 😎 🤝

"""

    keyboard = [
        [InlineKeyboardButton("👨‍💼 Admin", url="https://t.me/Jigar0648?text=I%20want%20to%20Join%20VIP")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            reply_markup=reply_markup
        )
        logger.info(f"Sent welcome message to {user.full_name}")
    except Exception as e:
        logger.warning(f"Couldn't send DM to {user.full_name}: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and update.effective_chat.type == "private":
        await send_welcome_message(context, update.effective_user, update.effective_chat.id)


async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    if request is None or request.chat.id != CHANNEL_ID:
        return
    user = request.from_user

    # Telegram's temporary DM permission ends once the request is processed.
    # A failed welcome must never prevent approval.
    await send_welcome_message(context, user, request.user_chat_id)
    try:
        await context.bot.approve_chat_join_request(request.chat.id, user.id)
        logger.info(f"Approved join request from {user.id} ({user.full_name})")
    except Exception:
        logger.exception(f"Failed to approve join request for {user.id}")
        return

    # A storage error must not interrupt welcome delivery or approval.
    try:
        save_user(user.id)
        left_users = load_json_file(LEFT_FILE)
        if str(user.id) in left_users:
            del left_users[str(user.id)]
            save_json_file(LEFT_FILE, left_users)
            logger.info(f"User {user.id} rejoined, removed from left_users")
    except Exception:
        logger.exception(f"Could not save membership data for {user.id}")


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
    f"📈 Hey {first_name}!\n\n"
    "YOU JUST LEFT “ TRADE WITH JIGAR ”\n\n"
    "Maybe it’s not the right time now — no worries 🤝\n\n"
    "But remember, our VIP members are making daily profit and recovering losses using AI software-based signals 📊\n\n"
    "Whenever you're ready to start again, you can join back from here 👇\n\n"
    "https://t.me/+_feJE83TCNJlZmFl\n\n"
    "🔹 Need help or have any questions?\n\n"
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
        await app.update_queue.put(update)
    except Exception as e:
        logger.error(f"Failed to process update: {e}")
        return web.Response(status=500, text="Update processing failed")
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
    return runner

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

async def check_who_left_loop(application):
    """Keep the existing reminders without requiring the optional JobQueue."""
    context = SimpleNamespace(bot=application.bot)
    await asyncio.sleep(10)
    while True:
        try:
            await check_who_left(context)
        except Exception:
            logger.exception("Membership check failed; will retry next cycle")
        await asyncio.sleep(60)


async def log_error(update, context):
    error = context.error
    logger.error("Unhandled update error", exc_info=(type(error), error, error.__traceback__))


async def main():
    global app
    if not BOT_TOKEN:
        raise RuntimeError("Set the BOT_TOKEN environment variable before starting the bot")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CommandHandler("start", start_command))
    app.add_error_handler(log_error)

    await app.initialize()
    await app.start()
    runner = None
    background_tasks = []
    try:
        runner = await run_web_server()
        await app.bot.set_webhook(
            WEBHOOK_URL,
            allowed_updates=["chat_join_request", "message"],
            drop_pending_updates=False,
        )
        logger.info("Webhook registered at %s", WEBHOOK_URL)
        background_tasks.append(asyncio.create_task(check_who_left_loop(app)))
        if RENDER_EXTERNAL_URL:
            background_tasks.append(asyncio.create_task(keep_alive_ping(RENDER_EXTERNAL_URL)))
        await asyncio.Event().wait()
    finally:
        for task in background_tasks:
            task.cancel()
        for task in background_tasks:
            with suppress(asyncio.CancelledError):
                await task
        if runner is not None:
            await runner.cleanup()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    if sys.platform.startswith('win') and sys.version_info[:2] >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())



