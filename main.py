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
import aiohttp
from aiohttp import web

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Environment variables (Optional: Use os.getenv for production safety)

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
PORT = int(os.getenv("PORT", 10000))
SELF_URL = os.getenv("SELF_URL", "https://jigarbot.onrender.com")  # Replace for Render

# ✅ Function to approve join requests and send welcome DM
async def approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat
    logger.info(f"Join request from {user.full_name} in {chat.title}")

    await update.chat_join_request.approve()

    welcome_text = f"""
👋 Hi {user.first_name}!

Welcome to 👑 *{chat.title}* 👑 

🏆 Join our VIP and Get daily 🏆 

▪️ 8–10 accurate signals (90% win rate)
▪️ Fast deposit & withdrawal ♻️
▪️ Free giveaways & strategies 📊
▪️ Personal support anytime ✅
💵 Start earning today 💵

(1) Register from this link ⬇️
👉 https://broker-qx.pro/sign-up/?lid=297045

(2) Deposit minimum $30 or above 💱

(3) Send your Trader ID : @jigar0648 ✅️

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

# ✅ Simple health check endpoint for uptime monitoring
async def handle_health(request):
    return web.Response(text="✅ Bot is running!")

# ✅ Periodic ping to keep the app awake
async def periodic_ping():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(f"{SELF_URL}/") as resp:
                    logger.info(f"Pinged self: {resp.status}")
            except Exception as e:
                logger.warning(f"Ping failed: {e}")
            await asyncio.sleep(60)  # Ping every 60 seconds

# ✅ Main function to run the bot and web server
async def main():
    # Windows event loop fix
    if sys.platform.startswith('win') and sys.version_info[:2] >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(ChatJoinRequestHandler(approve_join_request))
    app.add_handler(ChatMemberHandler(handle_member_status, ChatMemberHandler.CHAT_MEMBER))

    # ✅ Start the web server
    web_app = web.Application()
    web_app.add_routes([web.get("/", handle_health)])
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, port=PORT)
    await site.start()
    logger.info(f"Web server running on port {PORT}")

    # ✅ Run bot and periodic pings together
    await asyncio.gather(
        app.run_polling(),
        periodic_ping()
    )

# ✅ Start the async main function
if __name__ == '__main__':
    asyncio.run(main())
