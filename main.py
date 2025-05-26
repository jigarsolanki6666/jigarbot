import logging
import os
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    ChatMemberHandler,
    ContextTypes,
)
from aiohttp import web

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # Render injects this for web service
WEBHOOK_PATH = "/telegram"  # You can customize if needed
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}" if RENDER_EXTERNAL_URL else ""

app = None  # Global app reference for webhook processing


# ✅ Function to approve join requests and send welcome DM
async def approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat
    logger.info(f"Join request from {user.full_name} in {chat.title}")

    await update.chat_join_request.approve()

    welcome_text = f"""
👋 Hi {user.first_name}!

📊 WELCOME TO TRADE WITH JIGAR 📊

Do you have losses in trading ?

Then don’t worry — I will help you recover it all 🤝

Our VIP members are making 20% profit daily with highly accurate signals provided by my unique AI signal software 💻

So... ready to recover and grow fast ? 📈

Message me now : @JIGAR0648 ✅

Limited VIP spots — don’t miss out ⚠️

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

# ✅ Function to detect when user leaves/kicked & send farewell DM
async def handle_member_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.chat_member
    user = chat_member.from_user
    status = chat_member.new_chat_member.status

    if chat_member.chat.id != CHANNEL_ID:
        return

    if status in ['left', 'kicked']:
        logger.info(f"{user.full_name} left or was kicked from the channel.")
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=f"Goodbye {user.first_name}! 👋\nSorry to see you leave *{chat_member.chat.title}*.",
                parse_mode="Markdown"
            )
            logger.info(f"Sent farewell message to {user.full_name}")
        except Exception as e:
            logger.warning(f"Couldn't send farewell DM to {user.full_name}: {e}")

# ✅ HTTP health check endpoint
async def handle_health(request):
    return web.Response(text="Bot is alive and running! 🚀")

# ✅ Telegram webhook handler
async def handle_telegram_webhook(request):
    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
    return web.Response(text="OK")

# ✅ Run the aiohttp web server
async def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    web_app = web.Application()
    web_app.router.add_get('/', handle_health)
    web_app.router.add_post(WEBHOOK_PATH, handle_telegram_webhook)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"HTTP server running on port {port}")

# ✅ Main function
async def main():
    global app
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ✅ Register handlers
    app.add_handler(ChatJoinRequestHandler(approve_join_request))
    app.add_handler(ChatMemberHandler(handle_member_status, ChatMemberHandler.CHAT_MEMBER))

    logger.info("Starting bot and setting webhook...")

    await app.initialize()
    await app.bot.set_webhook(WEBHOOK_URL)
    await app.start()

    # ✅ Start web server to receive webhook updates
    await run_web_server()

    # ✅ Keep running
    stop_event = asyncio.Event()
    await stop_event.wait()

    # ✅ Graceful shutdown
    await app.stop()
    await app.shutdown()

# ✅ Entry point
if __name__ == '__main__':
    if sys.platform.startswith('win') and sys.version_info[:2] >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
