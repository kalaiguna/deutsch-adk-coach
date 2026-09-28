"""B2 German Conversation Agent using Google ADK & Gemini."""
import logging
from google import genai
from google.genai import types
from src import config
from src.agents.prompts import CONVERSATION_SYSTEM_PROMPT
from src.tools.firestore_tool import validate_and_save_session

logger = logging.getLogger(__name__)

class ConversationAgent:
    """Stateful B2 German Conversation Coach Agent."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = config.DEFAULT_MODEL
        
        # Tools available to the agent
        self.tools = [validate_and_save_session]
        
        # Initialize multi-turn chat session with system instruction
        self.chat = self.client.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=CONVERSATION_SYSTEM_PROMPT,
                temperature=0.7,
            )
        )

    def send_message(self, user_text: str) -> str:
        """Processes a text turn from the learner."""
        response = self.chat.send_message(user_text)
        return response.text

    def send_audio(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        """Processes an audio voice note from the learner."""
        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=mime_type
        )
        prompt_instruction = (
            "The user sent a spoken voice note in German. "
            "1. Transcribe the user's spoken words. "
            "2. Follow your standard response cycle: evaluate mistakes with category labels, "
            "provide the 🇩🇪 **B2-Umformulierung:**, and ask exactly one follow-up question."
        )
        response = self.chat.send_message([audio_part, prompt_instruction])
        return response.text
