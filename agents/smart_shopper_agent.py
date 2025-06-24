from google.adk.agents import LlmAgent
from agents.smart_shopper_prompt import SMART_SHOPPER_SYSTEM_PROMPT
from SocketCreate import sio

from agents.agent_tool_functions import (
    parse_transcript,
    find_deals,
    compare_deals
)

import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

#MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-1.5-pro-002"
MODEL = "gemini-2.5-flash-preview-05-20"
smart_shopper_agent = LlmAgent(
    model=MODEL,
    name="smart_shopper_agent",
    description="Generates and manages shopping lists, Help find deals for gadgets, clothes, etc.",
    instruction=SMART_SHOPPER_SYSTEM_PROMPT,
    tools=[parse_transcript, find_deals, compare_deals]
)


# In social_life_agent.py
async def test_smart_shopper_agent(query: str):
    smart_shopper_agent = LlmAgent(
        model=MODEL,
        name="smart_shopper_agent",
        instruction=SMART_SHOPPER_SYSTEM_PROMPT,
    )
    response = await smart_shopper_agent.generate_response(query)
    print(f"Smart Shopper Agent response: {response}")
    return response