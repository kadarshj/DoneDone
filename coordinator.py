from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from SocketCreate import sio
from google.adk.agents import ParallelAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agents.tools import sales_tool, grocery_tool, journal_tool, health_tracker_tool, mood_insight_tool, social_life_tool, smart_shopper_tool, coordinator_tool, client_intel_tool, proposal_drafting_tool, meeting_summarizer_tool
from database import User_query_collection
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
from prompts import return_instructions_root as get_instructions_root

load_dotenv()


os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

#MODEL = "gemini-2.5-pro-preview-05-06"
#MODEL = "gemini-1.5-pro-002"
MODEL = "gemini-2.5-flash-preview-05-20"


#APP_NAME = "multiagent_system"
#USER_ID = "user_001"

# Initialize session service at module level
#session_service = InMemorySessionService()

def create_coordinator_agent() -> LlmAgent:
    """Create the root coordinator agent."""
    print('Coordinator Agent processing...')
    
    # Load coordinator instruction
    COORDINATOR_INSTRUCTION = get_instructions_root()
    
    # Create LlmAgent that knows about both tools
    return LlmAgent(
        model=MODEL,
        name="coordinator_agent",
        instruction=COORDINATOR_INSTRUCTION,
        tools=[sales_tool, grocery_tool, journal_tool],
    )


async def process_user_query_simple(user_query: str, sid: str) -> str:
    app_name = "multiagent_system"
    user_id = "user_001"
    
    await sio.emit('Agent', {'type':"Grocery Agent", "Status": "Initiated", 'response': 'Grocery Agent initiating the process.'}, to=sid)
    await sio.emit('Agent', {'type':"Sales Agent", "Status": "Initiated", 'response': 'Sales Agent initiating the process.'}, to=sid)
    await sio.emit('Agent', {'type':"Journal Agent", "Status": "Initiated", 'response': 'Journal Agent initiating the process.'}, to=sid)

    try:
        print(f"Processing query for session {sid}: {user_query[:50]}...")
        await sio.emit('message', {'detail': 'Coordinator Agent processing...'}, to=sid)
        
        local_session_service = InMemorySessionService()
        coordinator = create_coordinator_agent()
        
        session_id = f"session_{int(time.time() * 1000)}"
        print(f"Creating session: {session_id}")
        
        await local_session_service.create_session(
            app_name=app_name, 
            user_id=user_id, 
            session_id=session_id
        )
        
        runner = Runner(
            agent=coordinator,
            app_name=app_name,
            session_service=local_session_service
        )
        
        user_content = types.Content(
            role='user', 
            parts=[types.Part(text=user_query)]
        )
        
        #print(f"Executing query: {user_query}")
        
        final_response = {"journal": "","sales": "", "grocery": "", "delegation": ""}
        response_emitted = False  # Track if response has been emitted
        async for event in runner.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=user_content
        ):
            print(f"Event received: {event}")
            print(f"Event attributes: {dir(event)}")
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.function_call:
                        # Store task delegation
                        final_response["delegation"] += f"{part.function_call.name}: {part.function_call.args.get('request')}\n"
                        print(f"Function call: {part.function_call.name} with args: {part.function_call.args}")
                    elif part.function_response:
                        # Store sub-agent responses
                        print(f"Function response: {part.function_response.name} with result: {part.function_response.response}")
                        if part.function_response.name == "sales_agent":
                            final_response["sales"] = part.function_response.response.get("result", "")
                            await sio.emit('message', {'detail': 'Sales Agent processing...'}, to=sid)
                        elif part.function_response.name == "grocery_agent":
                            final_response["grocery"] = part.function_response.response.get("result", "")
                            await sio.emit('message', {'detail': 'Grocery Agent processing...'}, to=sid)
                        elif part.function_response.name == "journal_agent":
                            final_response["journal"] = part.function_response.response.get("result", "")
                            await sio.emit('message', {'detail': 'Journal Agent processing...'}, to=sid)
                    elif part.text:
                        # Skip redundant JSON text events
                        if part.text.startswith('```json'):
                            print("Skipping redundant JSON text event")
                            continue
                        print(f"Text response: {part.text}")
            
            # Emit response only once when all three sub-agent responses are received
            if final_response["journal"] and final_response["sales"] and final_response["grocery"] and not response_emitted:
                #response_text = f"Task Delegation:\n{final_response['delegation'] or 'No delegation details captured.'}\n\nGrocery List:\n{final_response['grocery'] or 'No response received from grocery agent.'}\n\nElectronics Sales:\n{final_response['sales'] or 'No response received from sales agent.'}"
                #print(f"Emitting final response: {response_text[:100]}...")
                #await sio.emit('message', {'detail': response_text}, to=sid)
                #await sio.emit('message', {'task_delegation': final_response['delegation'] or 'No delegation details captured.'}, to=sid)
                #await sio.emit('message', {'grocery_agent': final_response['grocery'] or 'No response received from grocery agent.'}, to=sid)
                #await sio.emit('message', {'sales_agent': final_response['sales'] or 'No response received from sales agent.'}, to=sid)
                await sio.emit('Agent', {'type':"Coordinator Agent", "Status": "Completed", 'response': final_response['delegation'] or 'No delegation details captured.'}, to=sid)
                await sio.emit('Agent', {'type':"Grocery Agent", "Status": "Completed", 'response': final_response['grocery'] or 'No response received from grocery agent.'}, to=sid)
                await sio.emit('Agent', {'type':"Sales Agent", "Status": "Completed", 'response': final_response['sales'] or 'No response received from sales agent.'}, to=sid)
                await sio.emit('Agent', {'type':"Journal Agent", "Status": "Completed", 'response': final_response['journal'] or 'No response received from sales agent.'}, to=sid)
                response_emitted = True
                break
        
        return final_response["journal"] and final_response["sales"] and final_response["grocery"] and response_text or "No response received from agents"
    
    except Exception as e:
        print(f"Error processing query: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"


def create_instructor_agent(user_id, email) -> LlmAgent:
    """Create the root instructor agent."""
    print('instructor Agent processing...')
    
    # Load instructor instruction
    COORDINATOR_INSTRUCTION = get_instructions_root()
    # Create LlmAgent that knows about both tools
    return LlmAgent(
        model=MODEL,
        name="instructor_agent",
        instruction=COORDINATOR_INSTRUCTION,
        tools=[health_tracker_tool, mood_insight_tool, social_life_tool, smart_shopper_tool, coordinator_tool],
    )


async def process_user_query_simple_agent(user_query: str, user_id: str, email: str) -> str:
    app_name = "multiagent_systems"
    user_id = user_id

    try:
        #print(f"Processing query for session {sid}: {user_query[:50]}...")
        #await sio.emit('message', {'detail': 'instructor Agent processing...'}, to=sid)
        
        local_session_service = InMemorySessionService()
        instructor = create_instructor_agent(user_id, email)
        
        session_id = f"session_{int(time.time() * 1000)}"
        print(f"Creating session: {session_id}")
        
        await local_session_service.create_session(
            app_name=app_name, 
            user_id=user_id, 
            state={"user_id": user_id, "email": email},
            session_id=session_id
        )
        
        runner = Runner(
            agent=instructor,
            app_name=app_name,
            session_service=local_session_service
        )
        
        user_content = types.Content(
            role='user', 
            parts=[types.Part(text=user_query)]
        )
        
        #print(f"Executing query: {user_query}")
        
        final_response = {"socialLifeAgent": "", "healthTrackerAgent": "", "smartShopperAgent": "", "moodInsightAgent" : "", "coordinatorAgent" : "", "delegation": ""}
        response_emitted = False  # Track if response has been emitted
        async for event in runner.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=user_content
        ):
            print(f"Event received: {event}")
            print(f"Event attributes: {dir(event)}")
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.function_call:
                        # Store task delegation
                        final_response["delegation"] += f"{part.function_call.name}: {part.function_call.args.get('request')}\n"
                        print(f"Function call: {part.function_call.name} with args: {part.function_call.args}")
                    elif part.function_response:
                        # Store sub-agent responses
                        print(f"Function response: {part.function_response.name} with result: {part.function_response.response}")
                        if part.function_response.name == "social_life_agent":
                            final_response["socialLifeAgent"] = part.function_response.response.get("result", "")
                        elif part.function_response.name == "health_tracker_agent":
                            final_response["healthTrackerAgent"] = part.function_response.response.get("result", "")
                        elif part.function_response.name == "smart_shopper_agent":
                            final_response["smartShopperAgent"] = part.function_response.response.get("result", "")
                        elif part.function_response.name == "mood_insight_agent":
                            final_response["moodInsightAgent"] = part.function_response.response.get("result", "")
                        elif part.function_response.name == "coordinator_agent":
                            final_response["coordinatorAgent"] = part.function_response.response.get("result", "")
                    elif part.text:
                        # Skip redundant JSON text events
                        if part.text.startswith('```json'):
                            print("Skipping redundant JSON text event")
                            continue
                        print(f"Text response: {part.text}")
            
            # Emit response only once when both sub-agent responses are received
            if final_response["healthTrackerAgent"] and final_response["socialLifeAgent"] and final_response["moodInsightAgent"] and final_response["coordinatorAgent"] and final_response["smartShopperAgent"] and not response_emitted:
                #response_text = f"Task Delegation:\n{final_response['delegation'] or 'No delegation details captured.'}\n\nGrocery List:\n{final_response['grocery'] or 'No response received from grocery agent.'}\n\nElectronics Sales:\n{final_response['sales'] or 'No response received from sales agent.'}"
                #print(f"Emitting final response: {response_text[:100]}...")
                response_emitted = True
                break
        responseAgent = {"Task Delegation": final_response['delegation'] or 'No delegation details captured.',
                        "Agent": [
                            #{"type": "instructor Agent", 'response': final_response.get('delegation', 'Agent Not Applicable')},
                            {"type": "Health Tracker Agent", 'response': final_response.get('healthTrackerAgent', 'Agent Not Applicable')},
                            {"type": "Social Life Agent", 'response': final_response.get('socialLifeAgent', 'Agent Not Applicable')},
                            {"type": "Smart Shopper Agent", 'response': final_response.get('smartShopperAgent', 'Agent Not Applicable')},
                            {"type": "Mood Insight Agent", 'response': final_response.get('moodInsightAgent', 'Agent Not Applicable')},
                            {"type": "Coordinator Agent", 'response': final_response.get('coordinatorAgent', 'Agent Not Applicable')}
                        ]}
        #return final_response["journal"] and final_response["sales"] and final_response["grocery"] and response_text or "No response received from agents"
        user_query_res = {"user_query": user_query, "responseAgent": responseAgent, "created_at": datetime.utcnow()}
        result = await User_query_collection.insert_one(user_query_res)
        return responseAgent
    
    except Exception as e:
        print(f"Error processing query: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"


def create_instructor_agent_work(user_id, email) -> LlmAgent:
    """Create the root instructor agent."""
    print('instructor Agent processing...')
    
    # Load instructor instruction
    COORDINATOR_INSTRUCTION = get_instructions_root()
    COORDINATOR_INSTRUCTION += "\n\n user_id: " + user_id + "\n\n email: " + email
    # Create LlmAgent that knows about both tools
    return LlmAgent(
        model=MODEL,
        name="instructor_agent",
        instruction=COORDINATOR_INSTRUCTION,
        tools=[client_intel_tool, proposal_drafting_tool, meeting_summarizer_tool],
    )


async def process_user_query_simple_agent_work(user_query: str, user_id: str, email: str) -> str:
    app_name = "multiagent_systems"
    user_id = user_id

    try:
        #print(f"Processing query for session {sid}: {user_query[:50]}...")
        #await sio.emit('message', {'detail': 'instructor Agent processing...'}, to=sid)
        
        local_session_service = InMemorySessionService()
        instructor = create_instructor_agent_work(user_id, email)
        
        session_id = f"session_{int(time.time() * 1000)}"
        print(f"Creating session: {session_id}")
        
        await local_session_service.create_session(
            app_name=app_name, 
            user_id=user_id, 
            state={"user_id": user_id, "email": email},
            session_id=session_id
        )
        
        runner = Runner(
            agent=instructor,
            app_name=app_name,
            session_service=local_session_service
        )
        
        user_content = types.Content(
            role='user', 
            parts=[types.Part(text=user_query)]
        )
        
        #print(f"Executing query: {user_query}")
        
        final_response = {"clientIntelAgent": "", "proposalDraftingAgent": "", "meetingSummarizerAgent": "", "delegation": ""}
        response_emitted = False  # Track if response has been emitted
        async for event in runner.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=user_content
        ):
            print(f"Event received: {event}")
            print(f"Event attributes: {dir(event)}")
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.function_call:
                        # Store task delegation
                        final_response["delegation"] += f"{part.function_call.name}: {part.function_call.args.get('request')}\n"
                        print(f"Function call: {part.function_call.name} with args: {part.function_call.args}")
                    elif part.function_response:
                        # Store sub-agent responses
                        print(f"Function response: {part.function_response.name} with result: {part.function_response.response}")
                        if part.function_response.name == "client_intel_agent":
                            final_response["clientIntelAgent"] = part.function_response.response.get("result", "")
                        elif part.function_response.name == "proposal_drafting_agent":
                            final_response["proposalDraftingAgent"] = part.function_response.response.get("result", "")
                        elif part.function_response.name == "meeting_summarizer_agent":
                            final_response["meetingSummarizerAgent"] = part.function_response.response.get("result", "")
                    elif part.text:
                        # Skip redundant JSON text events
                        if part.text.startswith('```json'):
                            print("Skipping redundant JSON text event")
                            continue
                        print(f"Text response: {part.text}")
            
            # Emit response only once when both sub-agent responses are received
            if final_response["clientIntelAgent"] and final_response["proposalDraftingAgent"] and final_response["meetingSummarizerAgent"] and not response_emitted:
                response_text = f"Task Delegation:\n{final_response['delegation'] or 'No delegation details captured.'}\n\nGrocery List:\n{final_response['grocery'] or 'No response received from grocery agent.'}\n\nElectronics Sales:\n{final_response['sales'] or 'No response received from sales agent.'}"
                #print(f"Emitting final response: {response_text[:100]}...")
                response_emitted = True
                break
        '''responseAgent = {"Task Delegation": final_response['delegation'] or 'No delegation details captured.',
                        "Agent": [
                            {"type": "instructor Agent", 'response': final_response['delegation'] or 'No delegation details captured.'},
                            {"type": "Client Intel Agent", 'response': final_response['clientIntelAgent'] or 'Agent Not Applicable'},
                            {"type": "Proposal Drafting Agent", 'response': final_response['proposalDraftingAgent'] or 'Agent Not Applicable'},
                            {"type": "Meeting Summarizer Agent", 'response': final_response['meetingSummarizerAgent'] or 'Agent Not Applicable'}
                        ]}'''
        responseAgent = {"Task Delegation": final_response['delegation'] or 'No delegation details captured.',
                        "Agent": [
                            #{"type": "instructor Agent", 'response': final_response.get('delegation', 'Agent Not Applicable')},
                            {"type": "Client Intel Agent", 'response': final_response.get('clientIntelAgent', 'Agent Not Applicable')},
                            {"type": "Proposal Drafting Agent", 'response': final_response.get('proposalDraftingAgent', 'Agent Not Applicable')},
                            {"type": "Meeting Summarizer Agent", 'response': final_response.get('meetingSummarizerAgent', 'Agent Not Applicable')}
                        ]}
        #return final_response["journal"] and final_response["sales"] and final_response["grocery"] and response_text or "No response received from agents"
        user_query_res = {"user_query": user_query, "responseAgent": responseAgent, "created_at": datetime.utcnow()}
        result = await User_query_collection.insert_one(user_query_res)
        return responseAgent
    
    except Exception as e:
        print(f"Error processing query: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"
