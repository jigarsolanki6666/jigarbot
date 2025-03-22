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
# ✅ Your bot token from BotFather
#BOT_TOKEN = '7980614882:AAGqQzD55pC859_IIJfWgl2eN9H8DzUtX7s'  # Replace with your token
# ✅ Your channel ID (must be a negative number, e.g., -100...)
#CHANNEL_ID = -1001244012856  # Replace with your channel ID

# ✅ Function to approve join requests and send welcome DM
async def approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat
    logger.info(f"Join request from {user.full_name} in {chat.title}")

    await update.chat_join_request.approve()

    welcome_text = f"""
👋 Hi {user.first_name}!

Welcome to 👑 *{chat.title}* 👑 

       🏆 Join our vip and Get daily 🏆 

〰〰〰〰〰〰〰〰〰〰〰〰〰〰

▪️8–10 accurate signals (90% win rate) 
▪️Fast deposit & withdrawal ♻️
▪️Free giveaways & strategies 📊
▪️Personal support anytime ✅

💵 Start earning today 💵

➖➖➖➖➖➖➖➖➖➖➖➖➖➖

(1) Register from this link  ⬇️ 

https://broker-qx.pro/sign-up/?lid=297045

(2) Deposit minimum $30 or above 💰

(3) Send your Trader ID : @jigar0648

𝗟𝗲𝘁'𝘀 𝗴𝗿𝗼𝘄 𝘁𝗼𝗴𝗲𝘁𝗵𝗲𝗿 😎 🤝
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
async def handle(request):
    return web.Response(text="Bot is alive and running! 🚀")

async def run_web_server():
    port = int(os.environ.get('PORT', 10000))  # Render usually gives you the PORT env
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"HTTP server running on port {port}")

# ✅ Main function to run both bot and web server in parallel
async def main():
    # ✅ Create the application instance
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ✅ Register handlers
    app.add_handler(ChatJoinRequestHandler(approve_join_request))
    app.add_handler(ChatMemberHandler(handle_member_status, ChatMemberHandler.CHAT_MEMBER))

    logger.info("Bot is starting...")

    # ✅ Initialize and start the bot manually
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # ✅ Start the web server alongside the bot
    await run_web_server()

    # ✅ KEEP RUNNING FOREVER
    stop_event = asyncio.Event()
    await stop_event.wait()

    # ✅ Graceful shutdown when you exit the process manually
    await app.updater.stop()
    await app.stop()
    await app.shutdown()

# ✅ Entry point
if __name__ == '__main__':
    if sys.platform.startswith('win') and sys.version_info[:2] >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
