from google.adk.agents import LlmAgent
from agents.proposal_drafting_prompt import PROPOSAL_DRAFTING_SYSTEM_PROMPT
from SocketCreate import sio

from agents.agent_tool_functions import (
    retrieve_client_insights,
    generate_proposal,
    send_proposal_email
)

import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

#MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-1.5-pro-002"
MODEL = "gemini-2.5-flash-preview-05-20"
proposal_drafting_agent = LlmAgent(
    model=MODEL,
    name="proposal_drafting_agent",
    description="Drafts proposals based on client insights, Generate proposal (objectives, challenges, solution)",
    instruction=PROPOSAL_DRAFTING_SYSTEM_PROMPT,
    tools=[retrieve_client_insights, generate_proposal, send_proposal_email]
)


# In client_intel_agent.py
async def test_cproposal_drafting_agent(query: str):
    proposal_drafting_agent = LlmAgent(
        model=MODEL,
        name="proposal_drafting_agent",
        instruction=PROPOSAL_DRAFTING_SYSTEM_PROMPT,
    )
    response = await proposal_drafting_agent.generate_response(query)
    print(f"proposal_drafting_agent response: {response}")
    return response