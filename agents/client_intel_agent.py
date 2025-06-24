from google.adk.agents import LlmAgent
from agents.client_intel_prompt import CLIENT_INTEL_SYSTEM_PROMPT
from SocketCreate import sio

from agents.agent_tool_functions import (
    parse_client_transcript,
    store_client_insights
)

import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

#MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-1.5-pro-002"
MODEL = "gemini-2.5-flash-preview-05-20"
client_intel_agent = LlmAgent(
    model=MODEL,
    name="client_intel_agent",
    description="Extracts insights from client transcripts, Extract requirements from client conversations",
    instruction=CLIENT_INTEL_SYSTEM_PROMPT,
    tools=[parse_client_transcript, store_client_insights]
)


# In client_intel_agent.py
async def test_client_intel_agent(query: str):
    client_intel_agent = LlmAgent(
        model=MODEL,
        name="client_intel_agent",
        instruction=CLIENT_INTEL_SYSTEM_PROMPT,
    )
    response = await client_intel_agent.generate_response(query)
    print(f"client_intel_agent response: {response}")
    return response