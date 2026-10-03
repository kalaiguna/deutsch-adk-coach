"""Lektüre Agent — real German news article comprehension, 6-question sequence."""
from google.adk.agents import LlmAgent
from src import config
from src.agents.prompts import LEKTURE_SYSTEM_PROMPT
from src.tools.firestore_tool import validate_and_save_session
from src.tools.web_fetch_tool import fetch_article_text
from src.tools.web_search_tool import search_german_article

lekture_agent = LlmAgent(
    name="lekture_agent",
    model=config.DEFAULT_MODEL,
    instruction=LEKTURE_SYSTEM_PROMPT,
    tools=[search_german_article, fetch_article_text, validate_and_save_session],
)
