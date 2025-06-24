from google.adk.agents import LlmAgent
from agents.meeting_summarizer_prompt import MEETING_SUMMARIZER_SYSTEM_PROMPT
from SocketCreate import sio

from agents.agent_tool_functions import (
    parse_meeting_notes,
    generate_meeting_summary,
    store_meeting_summary
)

import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

#MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-1.5-pro-002"
MODEL = "gemini-2.5-flash-preview-05-20"
meeting_summarizer_agent = LlmAgent(
    model=MODEL,
    name="meeting_summarizer_agent",
    description="Summarizes meeting notes, Summarize meeting/diary notes",
    instruction=MEETING_SUMMARIZER_SYSTEM_PROMPT,
    tools=[parse_meeting_notes, generate_meeting_summary, store_meeting_summary]
)


# In client_intel_agent.py
async def test_meeting_summarizer_agent(query: str):
    meeting_summarizer_agent = LlmAgent(
        model=MODEL,
        name="meeting_summarizer_agent",
        instruction=PROPOSAL_DRAFTING_SYSTEM_PROMPT,
    )
    response = await meeting_summarizer_agent.generate_response(query)
    print(f"meeting_summarizer_agent response: {response}")
    return response