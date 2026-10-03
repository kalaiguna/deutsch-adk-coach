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
from src.agents.exam_prep import exam_prep_agent
from src.agents.grammar import grammar_agent
from src.agents.hoeren import hoeren_agent
from src.agents.lekture import lekture_agent
from src.agents.monthly_report import monthly_report_agent
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
grammar_runner = Runner(
    agent=grammar_agent,
    session_service=session_service,
    app_name=APP_NAME,
    auto_create_session=True,
)
monthly_report_runner = Runner(
    agent=monthly_report_agent,
    session_service=session_service,
    app_name=APP_NAME,
    auto_create_session=True,
)
exam_prep_runner = Runner(
    agent=exam_prep_agent,
    session_service=session_service,
    app_name=APP_NAME,
    auto_create_session=True,
)
lekture_runner = Runner(
    agent=lekture_agent,
    session_service=session_service,
    app_name=APP_NAME,
    auto_create_session=True,
)
hoeren_runner = Runner(
    agent=hoeren_agent,
    session_service=session_service,
    app_name=APP_NAME,
    auto_create_session=True,
)

RUNNERS = {
    "conversation": conversation_runner,
    "vocab": vocab_runner,
    "quiz": quiz_runner,
    "grammar": grammar_runner,
    "report": monthly_report_runner,
    "exam": exam_prep_runner,
    "lekture": lekture_runner,
    "hoeren": hoeren_runner,
}

# --- Per-user state ---
user_mode: dict[int, str] = {}          # "conversation" | "vocab" | "quiz" | "grammar" | "report" | "exam" | "lekture" | "hoeren"
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
    elif mode == "grammar":
        instruction = (
            "The user sent a spoken voice note. "
            "Transcribe it and treat it as their grammar exercise answer."
        )
    elif mode == "exam":
        instruction = (
            "The user sent a spoken voice note. "
            "Transcribe it and treat it as their spoken exam answer. "
            "Evaluate register, B2 structure usage, and fluency as appropriate for the active component."
        )
    elif mode in ("lekture", "hoeren"):
        instruction = (
            "The user sent a spoken voice note. "
            "Transcribe it and treat it as their answer. "
            "Respond appropriately for the active reading or listening exercise."
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
        "Commands: /vocab — vocab drill | /quiz — adaptive quiz | /grammatik — grammar | /bericht — monthly report | /pruefung — exam prep | /lektuere — reading | /hoeren — listening | /finish — end & save session"
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


async def lekture_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    user_mode[user_id] = "lekture"
    session_id = reset_session_id(user_id, "lekture")

    content = types.Content(
        role="user",
        parts=[types.Part(text="Find a current German news article and start the reading session.")],
    )

    lock = get_or_create_lock(user_id)
    async with lock:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await run_agent(lekture_runner, user_id, session_id, content)

    if reply:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("📰 Searching for a German article...")


async def hoeren_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    user_mode[user_id] = "hoeren"
    session_id = reset_session_id(user_id, "hoeren")

    content = types.Content(
        role="user",
        parts=[types.Part(text="Find a DW or Easy German episode and start the listening session.")],
    )

    lock = get_or_create_lock(user_id)
    async with lock:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await run_agent(hoeren_runner, user_id, session_id, content)

    if reply:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("🎧 Searching for a listening episode...")


async def pruefung_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    user_mode[user_id] = "exam"
    session_id = reset_session_id(user_id, "exam")

    content = types.Content(
        role="user",
        parts=[types.Part(text="Show me the exam prep components and let me choose one.")],
    )

    lock = get_or_create_lock(user_id)
    async with lock:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await run_agent(exam_prep_runner, user_id, session_id, content)

    if reply:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("📝 Starting telc B2 exam prep...")


async def grammatik_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    user_mode[user_id] = "grammar"
    session_id = reset_session_id(user_id, "grammar")

    content = types.Content(
        role="user",
        parts=[types.Part(text="Start the grammar session for this month's topic now.")],
    )

    lock = get_or_create_lock(user_id)
    async with lock:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await run_agent(grammar_runner, user_id, session_id, content)

    if reply:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("🇩🇪 Starten wir die Grammatikstunde!\n\n🇬🇧 Starting your grammar session...")


async def bericht_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    user_mode[user_id] = "report"
    session_id = reset_session_id(user_id, "report")

    content = types.Content(
        role="user",
        parts=[types.Part(text="Generate my monthly Monatsrückblick report now.")],
    )

    lock = get_or_create_lock(user_id)
    async with lock:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await run_agent(monthly_report_runner, user_id, session_id, content)

    if reply:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("📊 Generating your monthly report...")


async def finish_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    runner, session_id = _get_runner_and_session(user_id)
    content = types.Content(role="user", parts=[types.Part(text="/finish")])

    lock = get_or_create_lock(user_id)
    async with lock:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await run_agent(runner, user_id, session_id, content)

    await update.message.reply_text(reply or "✅ Session ended.")


async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = "/start · /vocab · /quiz · /grammatik · /bericht · /pruefung · /lektuere · /hoeren · /finish"
    await update.message.reply_text(f"Unknown command. Available commands:\n{commands}")


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

    await update.message.reply_text(reply or "⚠️ No response from the coach. Please try again.")


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

    await update.message.reply_text(reply or "⚠️ No response from the coach. Please try again.")


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled exception in handler", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("⚠️ Something went wrong. Please try again.")


def main():
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found.")
        return

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("vocab", vocab_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("grammatik", grammatik_command))
    app.add_handler(CommandHandler("bericht", bericht_command))
    app.add_handler(CommandHandler("pruefung", pruefung_command))
    app.add_handler(CommandHandler("lektuere", lekture_command))
    app.add_handler(CommandHandler("hoeren", hoeren_command))
    app.add_handler(CommandHandler("finish", finish_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))
    app.add_error_handler(handle_error)

    logger.info("Deutsch ADK Coach started.")
    app.run_polling()


if __name__ == "__main__":
    main()
