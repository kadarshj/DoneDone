from google.adk.agents import LlmAgent
from agents.grocery_prompts import GROCERY_TASK_PROMPT, MEAL_PLANNING_PROMPT, GROCERY_SYSTEM_PROMPT, RECIPE_REQUEST_PROMPT, SHOPPING_OPTIMIZATION_PROMPT
from SocketCreate import sio
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

#MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-1.5-pro-002"
MODEL = "gemini-2.5-flash-preview-05-20"
#sio.emit('message', {'detail': 'grocery Agent processing'}, to=sid)
grocery_agent = LlmAgent(
    model=MODEL,
    name="grocery_agent",
    description="Generates and manages grocery lists",
    instruction=GROCERY_SYSTEM_PROMPT,
    #tools=[]  # Add any specific tools this agent might need
)



# In grocery_agent.py
async def test_grocery_agent(query: str):
    grocery_agent = LlmAgent(
        model=MODEL,
        name="grocery_agent",
        instruction=GROCERY_SYSTEM_PROMPT,
    )
    response = await grocery_agent.generate_response(query)
    print(f"Grocery Agent response: {response}")
    return response