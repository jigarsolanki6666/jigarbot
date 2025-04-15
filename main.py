import logging
import os
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
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
#WELCOME_IMAGE_URL = "1.jpg"  # Replace with a valid image URL
#SECOND_WELCOME_IMAGES = [
   # "2.jpg", "3.jpg", "4.jpg", "5.jpg",
    #"6.jpg", "7.jpg", "8.jpg", "9.jpg",
#]

app = None  # Global app reference for webhook processing

# ✅ Function to send the second welcome message with 8 images
#async def send_second_welcome_message(user_id, context: ContextTypes.DEFAULT_TYPE):
    # Caption for second message
   # second_caption = """
#*Success Speaks – Profits Talk* 🔥

#Our VIPs turned trades into dreams. Gadgets, lifestyle, freedom — all started with one choice  💸 💎

#Why not *YOU*? 😎

#💰 *Join VIP | Start earning* 💰

#🚀 *DM now | Limited slots:* @jigar0648
 #   """

    # Inline button for JOIN VIP
  #  keyboard = [[InlineKeyboardButton("JOIN VIP 🔥", url="https://t.me/jigar0648")]]
   # reply_markup = InlineKeyboardMarkup(keyboard)

    # Prepare media group (8 images)
    #media = [InputMediaPhoto(open(photo, 'rb')) for photo in SECOND_WELCOME_IMAGES]

    #try:
        # Send images as an album
     #   sent_media = await context.bot.send_media_group(chat_id=user_id, media=media)
        
        # Edit the caption for the first image in the album
      #  await context.bot.edit_message_caption(
       #     chat_id=user_id,
        #    message_id=sent_media[0].message_id,
         #   caption=second_caption,
          #  parse_mode="Markdown",
           # reply_markup=reply_markup
        #)
        #logger.info(f"Sent second welcome message to {user_id}")
    
    #except Exception as e:
     #   logger.warning(f"Couldn't send second welcome message to {user_id}: {e}")


# ✅ Function to approve join requests and send welcome DM
async def approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat
    logger.info(f"Join request from {user.full_name} in {chat.title}")

    await update.chat_join_request.approve()

    welcome_caption = f"""
👋 Hi {user.first_name}!

Welcome to 👑 *{chat.title}* 👑 

TRIED OTHER VIP CHANNELS AND STILL LOSING ? ⚠️  

BECAUSE THEIR METHODS ARE OUTDATED 😂🤙

🔹 JOIN TRADE WITH JIGAR’S VIP & GET :

◾ 8–10 LIVE SIGNALS DAILY WITH MULTIPLE EXPIRIES 👇

( 1 MINUTE TO 1 HOUR | 90%+ WIN RATE ) 

◾ SIGNALS POWERED BY MY PERSONAL AI SOFTWARE THAT TRACKS BROKER MANIPULATION AND TRAPS IN REAL-TIME 📊

◾ FAST WITHDRAWALS + FULL SUPPORT 

🔴 MESSAGE ME NOW – @JIGAR0648  

TRADE SMART 📊 TRADE WITH JIGAR 🤝
"""

    keyboard = [
        [InlineKeyboardButton("👨‍💼 Admin", url="https://t.me/Jigar0648?text=I%20want%20to%20Join%20VIP")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_photo(
            chat_id=user.id,
            #photo=WELCOME_IMAGE_URL,  # Image URL or file path
            caption=welcome_caption,  # Text moved to caption
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        logger.info(f"Sent welcome message to {user.full_name}")
                        # Send second message with 8 images
        await send_second_welcome_message(user.id, context)
        
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
