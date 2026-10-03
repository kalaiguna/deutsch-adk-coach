"""Quiz Agent — Fehler-Rewind adaptive quiz with Sticky Challenge."""
from google.adk.agents import LlmAgent
from src import config
from src.agents.prompts import QUIZ_SYSTEM_PROMPT
from src.tools.firestore_tool import read_recent_sessions

quiz_agent = LlmAgent(
    name="quiz_agent",
    model=config.DEFAULT_MODEL,
    instruction=QUIZ_SYSTEM_PROMPT,
    tools=[read_recent_sessions],
)
