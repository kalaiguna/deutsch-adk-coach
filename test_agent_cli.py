"""Standalone CLI runner to test agents locally without Telegram."""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config
from src.agents.conversation import conversation_agent
from src.agents.vocab_recall import vocab_recall_agent
from src.main import APP_NAME, conversation_runner, vocab_runner, session_service

RUNNERS = {"conversation": conversation_runner, "vocab": vocab_runner}

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
    print("Commands: /vocab  switch to vocab drill")
    print("          /start  reset conversation session")
    print("          exit    quit")
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
