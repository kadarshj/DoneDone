from google.adk.agents import LlmAgent
from agents.social_life_prompt import SOCIAL_LIFE_SYSTEM_PROMPT
from SocketCreate import sio

from agents.agent_tool_functions import (
    read_contacts,
    schedule_call_reminder,
    send_followup_email
)

import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

#MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-1.5-pro-002"
MODEL = "gemini-2.5-flash-preview-05-20"
social_life_agent = LlmAgent(
    model=MODEL,
    name="social_life_agent",
    description="Track and remind about social connections",
    instruction=SOCIAL_LIFE_SYSTEM_PROMPT,
    tools=[read_contacts, schedule_call_reminder, send_followup_email]  # Add any specific tools this agent might need
)


# In social_life_agent.py
async def test_social_life_agent(query: str):
    social_life_agent = LlmAgent(
        model=MODEL,
        name="social_life_agent",
        instruction=SOCIAL_LIFE_SYSTEM_PROMPT,
    )
    response = await social_life_agent.generate_response(query)
    print(f"Social Life Agent response: {response}")
    return response