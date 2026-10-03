"""Standalone CLI runner to test agents locally without Telegram."""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config
from src.main import APP_NAME, conversation_runner, exam_prep_runner, grammar_runner, hoeren_runner, lekture_runner, monthly_report_runner, quiz_runner, vocab_runner, session_service

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

USER_ID = "cli_tester"


async def run_turn(mode: str, session_id: str, text: str) -> str:
    from google.genai import types
    runner = RUNNERS[mode]
    content = types.Content(role="user", parts=[types.Part(text=text)])
    parts = []
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            parts.extend(p.text for p in event.content.parts if hasattr(p, "text") and p.text)
    return "".join(parts)


def new_session_id(mode: str) -> str:
    return f"{mode}_{USER_ID}_{int(time.time())}"


def main():
    print("=" * 52)
    print("  Deutsch B2 ADK Coach — Local CLI Test Runner  ")
    print("=" * 52)
    print("Commands: /vocab      switch to vocab drill")
    print("          /quiz       switch to adaptive quiz")
    print("          /grammatik  switch to grammar session")
    print("          /bericht    generate monthly report")
    print("          /pruefung   telc B2 exam prep")
    print("          /lektuere   reading session (real article)")
    print("          /hoeren     listening session (DW/Easy German)")
    print("          /start      reset conversation session")
    print("          exit        quit")
    print()

    if not config.GEMINI_API_KEY:
        print("[!] GEMINI_API_KEY not set. Copy .env.example to .env and set it.")
        sys.exit(1)

    mode = "conversation"
    session_id = new_session_id(mode)

    print(f"[+] Mode: {mode} | Session: {session_id}")
    print("[+] Agents loaded. Send your first message.\n")

    while True:
        try:
            user_input = input("You 👤: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("\nAuf Wiedersehen! 👋")
                break

            if user_input == "/start":
                mode = "conversation"
                session_id = new_session_id(mode)
                print(f"[+] New conversation session: {session_id}\n")
                continue

            if user_input == "/vocab":
                mode = "vocab"
                session_id = new_session_id(mode)
                print(f"[+] Switched to vocab drill | Session: {session_id}")
                user_input = "Start the vocabulary recall drill now."

            elif user_input == "/quiz":
                mode = "quiz"
                session_id = new_session_id(mode)
                print(f"[+] Switched to adaptive quiz | Session: {session_id}")
                user_input = "Start the adaptive quiz now."

            elif user_input == "/grammatik":
                mode = "grammar"
                session_id = new_session_id(mode)
                print(f"[+] Switched to grammar session | Session: {session_id}")
                user_input = "Start the grammar session for this month's topic now."

            elif user_input == "/bericht":
                mode = "report"
                session_id = new_session_id(mode)
                print(f"[+] Generating monthly report | Session: {session_id}")
                user_input = "Generate my monthly Monatsrückblick report now."

            elif user_input == "/pruefung":
                mode = "exam"
                session_id = new_session_id(mode)
                print(f"[+] Switched to exam prep | Session: {session_id}")
                user_input = "Show me the exam prep components and let me choose one."

            elif user_input == "/lektuere":
                mode = "lekture"
                session_id = new_session_id(mode)
                print(f"[+] Switched to reading session | Session: {session_id}")
                user_input = "Find a current German news article and start the reading session."

            elif user_input == "/hoeren":
                mode = "hoeren"
                session_id = new_session_id(mode)
                print(f"[+] Switched to listening session | Session: {session_id}")
                user_input = "Find a DW or Easy German episode and start the listening session."

            print("\n[Thinking...]\n")
            reply = asyncio.run(run_turn(mode, session_id, user_input))

            if reply:
                print(f"🤖 Bot:\n{reply}\n")
            else:
                print("[!] No text response returned (tool call may have fired).\n")
            print("-" * 50)

        except KeyboardInterrupt:
            print("\nSession ended.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")


if __name__ == "__main__":
    main()
