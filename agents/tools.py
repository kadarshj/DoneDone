from google.adk.tools.agent_tool import AgentTool
from agents.sales_agent import sales_agent
from agents.grocery_agent import grocery_agent


# wrap each LlmAgent as a callable tool
sales_tool = AgentTool(agent=sales_agent)
grocery_tool = AgentTool(agent=grocery_agent)