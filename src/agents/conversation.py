"""B2 German Conversation Agent — ADK LlmAgent."""
from google.adk.agents import LlmAgent
from google.genai import types as genai_types
from src import config
from src.agents.prompts import CONVERSATION_SYSTEM_PROMPT
from src.tools.firestore_tool import validate_and_save_session

conversation_agent = LlmAgent(
    name="conversation_agent",
    model=config.DEFAULT_MODEL,
    instruction=CONVERSATION_SYSTEM_PROMPT,
    tools=[validate_and_save_session],
    generate_content_config=genai_types.GenerateContentConfig(temperature=0.7),
)
