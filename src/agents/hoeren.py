"""Hören Agent — DW/Easy German transcript comprehension and translation."""
from google.adk.agents import LlmAgent
from src import config
from src.agents.prompts import HOEREN_SYSTEM_PROMPT
from src.tools.firestore_tool import validate_and_save_session
from src.tools.web_fetch_tool import fetch_article_text
from src.tools.web_search_tool import search_german_article

hoeren_agent = LlmAgent(
    name="hoeren_agent",
    model=config.DEFAULT_MODEL,
    instruction=HOEREN_SYSTEM_PROMPT,
    tools=[search_german_article, fetch_article_text, validate_and_save_session],
)
