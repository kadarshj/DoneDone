from google.adk.agents import LlmAgent
from agents.mood_insight_prompt import MOOD_INSIGHT_SYSTEM_PROMPT
from SocketCreate import sio

from agents.agent_tool_functions import (
    detect_mood,
    suggest_content,
    send_mood_summary_email
)

import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

#MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-1.5-pro-002"
MODEL = "gemini-2.5-flash-preview-05-20"
mood_insight_agent = LlmAgent(
    model=MODEL,
    name="mood_insight_agent",
    description="Analyzes user mood and provides content suggestions, Log and trend emotional state",
    instruction=MOOD_INSIGHT_SYSTEM_PROMPT,
    tools=[detect_mood, suggest_content, send_mood_summary_email]
)


# In social_life_agent.py
async def test_mood_insight_agent(query: str):
    mood_insight_agent = LlmAgent(
        model=MODEL,
        name="mood_insight_agent",
        instruction=MOOD_INSIGHT_SYSTEM_PROMPT,
    )
    response = await mood_insight_agent.generate_response(query)
    print(f"Modd insight Agent response: {response}")
    return response