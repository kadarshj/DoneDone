from google.adk.tools.agent_tool import AgentTool
from agents.sales_agent import sales_agent
from agents.grocery_agent import grocery_agent
from agents.journal_agent import journal_agent

from agents.coordinator_agent import coordinator_agent
from agents.health_tracker_agent import health_tracker_agent
from agents.mood_insight_agent import mood_insight_agent
from agents.social_life_agent import social_life_agent
from agents.smart_shopper_agent import smart_shopper_agent

from agents.client_intel_agent import client_intel_agent
from agents.proposal_drafting_agent import proposal_drafting_agent
from agents.meeting_summarizer_agent import meeting_summarizer_agent

# wrap each LlmAgent as a callable tool
sales_tool = AgentTool(agent=sales_agent)
grocery_tool = AgentTool(agent=grocery_agent)
journal_tool = AgentTool(agent=journal_agent)

coordinator_tool = AgentTool(agent=coordinator_agent)
health_tracker_tool = AgentTool(agent=health_tracker_agent)
mood_insight_tool = AgentTool(agent=mood_insight_agent)
social_life_tool = AgentTool(agent=social_life_agent)
smart_shopper_tool = AgentTool(agent=smart_shopper_agent)

client_intel_tool = AgentTool(agent=client_intel_agent)
proposal_drafting_tool = AgentTool(agent=proposal_drafting_agent)
meeting_summarizer_tool = AgentTool(agent=meeting_summarizer_agent)