"""Exam Prep Agent — telc B2 practice: Schreiben, Sprechen, Trap Drill. No session save."""
from google.adk.agents import LlmAgent
from src import config
from src.agents.prompts import EXAM_PREP_SYSTEM_PROMPT

exam_prep_agent = LlmAgent(
    name="exam_prep_agent",
    model=config.DEFAULT_MODEL,
    instruction=EXAM_PREP_SYSTEM_PROMPT,
)
