"""Quick standalone CLI runner to test the B2 Conversation Coach without Telegram."""
import os
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config
from src.agents.conversation import ConversationAgent

def main():
    print("==================================================")
    print("   Deutsch B2 ADK Coach — Local CLI Test Runner   ")
    print("==================================================")
    
    if not config.GEMINI_API_KEY:
        print("[!] Error: GEMINI_API_KEY is not set.")
        print("Please copy .env.example to .env and set your GEMINI_API_KEY.")
        sys.exit(1)

    print("[+] Initializing Conversation Agent with Gemini...")
    agent = ConversationAgent(session_id="cli_tester")
    
    print("\n🤖 Bot: 🇩🇪 **Guten Tag! Wie läuft dein Tag bis jetzt?**")
    print("         🇬🇧 Good day! How is your day going so far?\n")
    
    print("Type your German response below (or 'exit' to quit):\n")
    
    while True:
        try:
            user_input = input("You 👤: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("\nAuf Wiedersehen! Tschüss! 👋")
                break
                
            print("\n[Thinking with Gemini...]\n")
            response = agent.send_message(user_input)
            print(f"🤖 Bot:\n{response}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\nSession ended.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    main()
