from google.adk.agents import LlmAgent
from agents.sales_prompts import SALES_SYSTEM_PROMPT, SALES_TASK_PROMPT, PRODUCT_RECOMMENDATION_PROMPT, PRICING_STRATEGY_PROMPT
from SocketCreate import sio
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

#MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-1.5-pro-002"
MODEL = "gemini-2.5-flash-preview-05-20"

sales_agent = LlmAgent(
    model=MODEL,
    name="sales_agent",
    description="Handles sales-related tasks",
    instruction=SALES_SYSTEM_PROMPT,
    #tools=[]  # Add any specific tools this agent might need
)


# In sales_agent.py
async def test_sales_agent(query: str):
    sales_agent = LlmAgent(
        model=MODEL,
        name="sales_agent",
        instruction=SALES_SYSTEM_PROMPT,
    )
    response = await sales_agent.generate_response(query)
    print(f"Sales Agent response: {response}")
    return response