"""Monthly Report Agent — Monatsrückblick aggregation and persistence."""
from google.adk.agents import LlmAgent
from src import config
from src.agents.prompts import MONTHLY_REPORT_SYSTEM_PROMPT
from src.tools.firestore_tool import read_recent_sessions, validate_and_save_session

monthly_report_agent = LlmAgent(
    name="monthly_report_agent",
    model=config.DEFAULT_MODEL,
    instruction=MONTHLY_REPORT_SYSTEM_PROMPT,
    tools=[read_recent_sessions, validate_and_save_session],
)
