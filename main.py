import logging
import os
import sys
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    ChatMemberHandler,
    ContextTypes,
)

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Your bot token from BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# ✅ Function to approve join requests and send welcome DM
async def approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat
    logger.info(f"Join request from {user.full_name} in {chat.title}")

    # Approve the request
    await update.chat_join_request.approve()

    # Welcome message
    welcome_text = f"""
👋 Hi {user.first_name}!

Welcome to 👑 *{chat.title}* 👑 

🏆 Join our VIP and Get daily 🏆 

〰〰〰〰〰〰〰〰〰〰〰〰〰〰

▪️ 8–10 accurate signals (90% win rate)

▪️ Fast deposit & withdrawal ♻️

▪️ Free giveaways & strategies 📊

▪️ Personal support anytime ✅

💵 Start earning today 💵

〰〰〰〰〰〰〰〰〰〰〰〰〰〰

(1) Register from this link ⬇️

👉 https://broker-qx.pro/sign-up/?lid=297045

(2) Deposit minimum $30 or above 💱

(3) Send your Trader ID : @jigar0648 ✅️

𝗟𝗲𝘁'𝘀 𝗴𝗿𝗼𝘄 𝘁𝗼𝗴𝗲𝘁𝗵𝗲𝗿 😎 🤝
"""

    # Inline button for contacting Admin with pre-filled message
    keyboard = [
        [InlineKeyboardButton("👨‍💼 Admin", url="https://t.me/Jigar0648?text=I%20want%20to%20Join%20VIP")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send a welcome message to their DM
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

    # Make sure it's the right channel
    if chat_member.chat.id != CHANNEL_ID:
        return

    # Detect leaving or kicked status
    if status in ['left', 'kicked']:
        logger.info(f"{user.full_name} left or was kicked from the channel.")

        # Send a farewell message to their DM
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=f"Goodbye {user.first_name}! 👋\nSorry to see you leave *{chat_member.chat.title}*.",
                parse_mode="Markdown"
            )
            logger.info(f"Sent farewell message to {user.full_name}")
        except Exception as e:
            logger.warning(f"Couldn't send farewell DM to {user.full_name}: {e}")

# ✅ Start the Telegram Bot in a thread
def start_bot():
    # Fix for Windows event loop policy
    if sys.platform.startswith('win') and sys.version_info[:2] >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(ChatJoinRequestHandler(approve_join_request))
    app.add_handler(ChatMemberHandler(handle_member_status, ChatMemberHandler.CHAT_MEMBER))

    logger.info("Bot is running...")

    app.run_polling()

# ✅ Minimal HTTP server to keep Render alive
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        message = "Bot is running!"
        self.wfile.write(message.encode())

# ✅ Start HTTP server in the main thread
def start_http_server():
    port = int(os.environ.get("PORT", 10000))  # Render sets PORT automatically
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    logger.info(f"HTTP Server running on port {port}")
    server.serve_forever()

# ✅ Main entry point
if __name__ == '__main__':
    # Start the bot in a background thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

    # Start the HTTP server (blocking)
    start_http_server()
