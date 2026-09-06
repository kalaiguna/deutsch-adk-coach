"""Telegram Bot entry point for Deutsch ADK Coach with concurrency lock."""
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from src import config
from src.agents.conversation import ConversationAgent

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Active user sessions and concurrency locks to prevent out-of-order execution
user_sessions: dict[int, ConversationAgent] = {}
user_locks: dict[int, asyncio.Lock] = {}

def get_or_create_lock(user_id: int) -> asyncio.Lock:
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]

def get_or_create_agent(user_id: int) -> ConversationAgent:
    if user_id not in user_sessions:
        user_sessions[user_id] = ConversationAgent(session_id=str(user_id))
    return user_sessions[user_id]

def is_authorized(user_id: int) -> bool:
    if not config.ALLOWED_TELEGRAM_USERS:
        return True
    return user_id in config.ALLOWED_TELEGRAM_USERS

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Unauthorized user.")
        return

    # Reset or create session
    user_sessions[user_id] = ConversationAgent(session_id=str(user_id))
    welcome_text = (
        "🇩🇪 **Guten Morgen! Willkommen bei deinem Deutsch B2 Sprachcoach.**\n\n"
        "🇬🇧 Good morning! Welcome to your German B2 language coach.\n\n"
        "💡 *Du kannst mir auf Deutsch schreiben oder Sprachnachrichten senden!*\n"
        "💡 *You can type in German or send voice notes anytime!*\n\n"
        "🇩🇪 **Worüber möchtest du heute sprechen? (Thema oder Arbeit?)**\n\n"
        "🇬🇧 What would you like to talk about today? (Topic or work?)"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    lock = get_or_create_lock(user_id)
    async with lock:
        agent = get_or_create_agent(user_id)
        user_text = update.message.text
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        reply = agent.send_message(user_text)
        await update.message.reply_text(reply)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    lock = get_or_create_lock(user_id)
    async with lock:
        agent = get_or_create_agent(user_id)
        
        # Show typing / recording action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="record_voice")
        
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        audio_bytearray = await voice_file.download_as_bytearray()
        
        reply = agent.send_audio(bytes(audio_bytearray), mime_type="audio/ogg")
        await update.message.reply_text(reply)

def main():
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found. Set it in .env or environment variables.")
        return

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    logger.info("Deutsch ADK Coach Telegram bot started listening...")
    app.run_polling()

if __name__ == "__main__":
    main()
