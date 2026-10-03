"""Telegram Bot entry point — ADK Runner-based multi-agent orchestration."""
import asyncio
import logging
import time
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from src import config
from src.agents.conversation import conversation_agent
from src.agents.quiz import quiz_agent
from src.agents.vocab_recall import vocab_recall_agent

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ADK setup ---
APP_NAME = "deutsch-adk-coach"
session_service = InMemorySessionService()

conversation_runner = Runner(
    agent=conversation_agent,
    session_service=session_service,
    app_name=APP_NAME,
    auto_create_session=True,
)
vocab_runner = Runner(
    agent=vocab_recall_agent,
    session_service=session_service,
    app_name=APP_NAME,
    auto_create_session=True,
)
quiz_runner = Runner(
    agent=quiz_agent,
    session_service=session_service,
    app_name=APP_NAME,
    auto_create_session=True,
)

RUNNERS = {"conversation": conversation_runner, "vocab": vocab_runner, "quiz": quiz_runner}

# --- Per-user state ---
user_mode: dict[int, str] = {}          # "conversation" | "vocab" | "quiz"
user_session_ids: dict[int, dict] = {}  # {user_id: {mode: session_id}}
user_locks: dict[int, asyncio.Lock] = {}


def get_or_create_lock(user_id: int) -> asyncio.Lock:
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]


def get_or_create_session_id(user_id: int, mode: str) -> str:
    """Returns the current session ID for this user+mode, creating a stable one if none exists."""
    user_session_ids.setdefault(user_id, {})
    if mode not in user_session_ids[user_id]:
        user_session_ids[user_id][mode] = f"{mode}_{user_id}"
    return user_session_ids[user_id][mode]


def reset_session_id(user_id: int, mode: str) -> str:
    """Creates a fresh timestamped session ID, discarding the previous one."""
    sid = f"{mode}_{user_id}_{int(time.time())}"
    user_session_ids.setdefault(user_id, {})[mode] = sid
    return sid


def is_authorized(user_id: int) -> bool:
    if not config.ALLOWED_TELEGRAM_USERS:
        return True
    return user_id in config.ALLOWED_TELEGRAM_USERS


async def run_agent(runner: Runner, user_id: int, session_id: str, content: types.Content) -> str:
    """Run one agent turn and return the accumulated final text response."""
    final_parts = []
    async for event in runner.run_async(
        user_id=str(user_id),
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_parts.extend(
                p.text for p in event.content.parts if hasattr(p, "text") and p.text
            )
    return "".join(final_parts)


def _get_runner_and_session(user_id: int) -> tuple[Runner, str]:
    """Returns the active runner and session ID for the user's current mode."""
    mode = user_mode.get(user_id, "conversation")
    return RUNNERS[mode], get_or_create_session_id(user_id, mode)


def _voice_content(audio_bytes: bytes, mode: str) -> types.Content:
    """Builds a Content for a voice message, with mode-appropriate instruction."""
    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg")
    if mode == "conversation":
        instruction = (
            "The user sent a spoken voice note in German. "
            "1. Transcribe the user's spoken words. "
            "2. Follow your standard response cycle: evaluate mistakes with category labels, "
            "provide the 🇩🇪 **B2-Umformulierung:**, and ask exactly one follow-up question."
        )
    elif mode == "quiz":
        instruction = (
            "The user sent a spoken voice note. "
            "Transcribe it and treat it as their quiz answer."
        )
    else:
        instruction = (
            "The user sent a spoken voice note. "
            "Transcribe it and treat it as their drill answer."
        )
    return types.Content(role="user", parts=[audio_part, types.Part(text=instruction)])


# --- Telegram handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Unauthorized user.")
        return

    user_mode[user_id] = "conversation"
    reset_session_id(user_id, "conversation")

    welcome_text = (
        "🇩🇪 **Guten Morgen! Willkommen bei deinem Deutsch B2 Sprachcoach.**\n\n"
        "🇬🇧 Good morning! Welcome to your German B2 language coach.\n\n"
        "💡 *Du kannst mir auf Deutsch schreiben oder Sprachnachrichten senden!*\n"
        "💡 *You can type in German or send voice notes anytime!*\n\n"
        "🇩🇪 **Worüber möchtest du heute sprechen?**\n\n"
        "🇬🇧 What would you like to talk about today?\n\n"
        "Commands: /vocab — vocabulary drill | /quiz — adaptive quiz"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def vocab_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    user_mode[user_id] = "vocab"
    session_id = reset_session_id(user_id, "vocab")

    content = types.Content(
        role="user",
        parts=[types.Part(text="Start the vocabulary recall drill now.")],
    )

    lock = get_or_create_lock(user_id)
    async with lock:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await run_agent(vocab_runner, user_id, session_id, content)

    if reply:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("🇩🇪 Starten wir das Vokabeltraining!\n\n🇬🇧 Starting your vocab drill...")


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    user_mode[user_id] = "quiz"
    session_id = reset_session_id(user_id, "quiz")

    content = types.Content(
        role="user",
        parts=[types.Part(text="Start the adaptive quiz now.")],
    )

    lock = get_or_create_lock(user_id)
    async with lock:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await run_agent(quiz_runner, user_id, session_id, content)

    if reply:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("🎯 Starting your adaptive quiz...")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    runner, session_id = _get_runner_and_session(user_id)
    content = types.Content(role="user", parts=[types.Part(text=update.message.text)])

    lock = get_or_create_lock(user_id)
    async with lock:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await run_agent(runner, user_id, session_id, content)

    if reply:
        await update.message.reply_text(reply)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    mode = user_mode.get(user_id, "conversation")
    runner, session_id = _get_runner_and_session(user_id)

    voice_file = await context.bot.get_file(update.message.voice.file_id)
    audio_bytes = bytes(await voice_file.download_as_bytearray())
    content = _voice_content(audio_bytes, mode)

    lock = get_or_create_lock(user_id)
    async with lock:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="record_voice")
        reply = await run_agent(runner, user_id, session_id, content)

    if reply:
        await update.message.reply_text(reply)


def main():
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found.")
        return

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("vocab", vocab_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info("Deutsch ADK Coach started.")
    app.run_polling()


if __name__ == "__main__":
    main()
