from google.adk.agents import LlmAgent
from agents.health_tracker_prompt import HEALTH_TRACKER_SYSTEM_PROMPT
from SocketCreate import sio

from agents.agent_tool_functions import (
    update_health_metrics,
    set_health_reminder,
    send_progress_email
)

import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

#MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-1.5-pro-002"
MODEL = "gemini-2.5-flash-preview-05-20"
health_tracker_agent = LlmAgent(
    model=MODEL,
    name="health_tracker_agent",
    description="Track personal improvement goals (BMI, habits)",
    instruction=HEALTH_TRACKER_SYSTEM_PROMPT,
    tools=[update_health_metrics, set_health_reminder, send_progress_email]
)


# In social_life_agent.py
async def test_health_tracker_agent(query: str):
    health_tracker_agent = LlmAgent(
        model=MODEL,
        name="health_tracker_agent",
        instruction=HEALTH_TRACKER_SYSTEM_PROMPT,
    )
    response = await health_tracker_agent.generate_response(query)
    print(f"Health Tracker Agent response: {response}")
    return response