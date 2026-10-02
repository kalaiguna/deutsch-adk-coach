"""Vocabulary Recall Agent — SRS-style drill from recent session misses."""
from google.adk.agents import LlmAgent
from src import config
from src.agents.prompts import VOCAB_RECALL_SYSTEM_PROMPT
from src.tools.firestore_tool import read_recent_sessions

vocab_recall_agent = LlmAgent(
    name="vocab_recall_agent",
    model=config.DEFAULT_MODEL,
    instruction=VOCAB_RECALL_SYSTEM_PROMPT,
    tools=[read_recent_sessions],
)
