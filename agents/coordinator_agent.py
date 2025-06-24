from google.adk.agents import LlmAgent
from agents.coordinator_prompt import COORDINATOR_SYSTEM_PROMPT
from SocketCreate import sio

from agents.agent_tool_functions import (
    aggregate_tasks,
    compile_report,
    send_report_email,
    get_user_email
)

import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

#MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-1.5-pro-002"
MODEL = "gemini-2.5-flash-preview-05-20"
coordinator_agent = LlmAgent(
    model=MODEL,
    name="coordinator_agent",
    description="Coordinates tasks across agents, Summarize all agent tasks into a daily log",
    instruction=COORDINATOR_SYSTEM_PROMPT,
    tools=[aggregate_tasks, compile_report, get_user_email, send_report_email]
)


# In social_life_agent.py
async def test_coordinator_agent(query: str):
    coordinator_agent = LlmAgent(
        model=MODEL,
        name="coordinator_agent",
        instruction=COORDINATOR_SYSTEM_PROMPT,
    )
    response = await coordinator_agent.generate_response(query)
    print(f"Coordinator Agent response: {response}")
    return response