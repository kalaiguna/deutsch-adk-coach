"""Grammar Agent — 12-topic monthly rotation with structured exercises."""
from google.adk.agents import LlmAgent
from src import config
from src.agents.prompts import GRAMMAR_SYSTEM_PROMPT
from src.tools.firestore_tool import read_recent_sessions

grammar_agent = LlmAgent(
    name="grammar_agent",
    model=config.DEFAULT_MODEL,
    instruction=GRAMMAR_SYSTEM_PROMPT,
    tools=[read_recent_sessions],
)
