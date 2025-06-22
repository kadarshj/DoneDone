from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import socketio
from SocketCreate import sio   # Import the shared sio instance
from database import users_collection, ping_server
from models import User, UserInDB, OTPRequest, OTPVerify, Token, SignupVerifyRequest, OTPVerifyLogin, RefreshToken, QueryRequest, QueryResponse
from auth import generate_otp, verify_otp, create_access_token, create_refresh_token, get_current_user, refresh_access_token
# Import the async function
from coordinator import process_user_query_simple, process_user_query_simple_agent
from bson import ObjectId
import asyncio
import os
from dotenv import load_dotenv
from jose import jwt
from urllib.parse import parse_qs
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
import json

load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# ✅ Allowed origins (Change to match your frontend URL)
origins = [
    "http://localhost:5173",  # React, Next.js frontend (development)
    "http://127.0.0.1:5173",  # Alternative local address
    "https://donedone.aminobots.com",  # Production frontend domain
]

# ✅ Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specific origins
    allow_credentials=True,  # Allow cookies & authentication
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)
# Initialize Socket.IO server with JWT authentication
#sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)
app.mount("/socket.io", socket_app)

# Ensure MongoDB connection on startup
@app.on_event("startup")
async def startup_event():
    await ping_server()

# --- REST API Endpoints ---

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Hello World"}

@app.post("/signup/request-otp/", response_model=QueryResponse)
async def signup_request_otp(otp_request: OTPRequest):
    """Request OTP for signup"""
    existing_user = await users_collection.find_one({"email": otp_request.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    await generate_otp(otp_request.email, purpose="signup")
    return {"status": "success", "message": "OTP sent to your email"}

@app.post("/signup/verify-otp/", response_model=Token)
async def signup_verify_otp(data: SignupVerifyRequest):
    await verify_otp(data.email, data.otp, purpose="signup")
    user_dict = {"name": data.name, "email": data.email, "otp": data.otp, "created_at": datetime.utcnow()}
    result = await users_collection.insert_one(user_dict)
    #user_dict["id"] = str(result.inserted_id)
    #return user_dict
    access_token = await create_access_token({"sub": data.email})
    refresh_token = await create_refresh_token({"sub": data.email})
    return {"status": "success", "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post("/login/request-otp/", response_model=QueryResponse)
async def login_request_otp(otp_request: OTPRequest):
    """Request OTP for login"""
    user = await users_collection.find_one({"email": otp_request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await generate_otp(otp_request.email, purpose="login")
    return {"status": "success", "message": "OTP sent to your email"}

@app.post("/login/verify-otp/", response_model=Token)
async def login_verify_otp(otp_verify: OTPVerifyLogin):
    """Verify OTP and generate access and refresh tokens"""
    await verify_otp(otp_verify.email, otp_verify.otp, purpose="login")

    # Update login timestamp
    await users_collection.update_one(
        {"email": otp_verify.email},
        {"$set": {"last_login_at": datetime.utcnow(), "otp": otp_verify.otp}}
    )

    access_token = await create_access_token({"sub": otp_verify.email})
    refresh_token = await create_refresh_token({"sub": otp_verify.email})
    return {"status": "success", "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post("/refresh/", response_model=Token)
async def refresh_token(RefreshToken: RefreshToken):
    """Refresh access token using refresh token"""
    access_token = await refresh_access_token(RefreshToken.refresh_token)
    return {"status": "success", "access_token": access_token, "refresh_token": RefreshToken.refresh_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=UserInDB)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@app.post("/users/agent/query/")
async def agent_query(payload: QueryRequest, current_user: dict = Depends(get_current_user)):
    """Handle user query through agent"""
    user_query = payload.user_query
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    print(f"Received query from {current_user['id']}: {user_query}")
    # Call the async function that handles the agent processing
    response = await process_user_query_simple_agent(user_query, current_user["id"])
    #return {"response": response}
    return response

# --- WebSocket Events ---

@sio.event
async def connect(sid, environ, auth=None):
    """Handle WebSocket connection with JWT authentication"""
    token = None
    # Check if token is in auth object
    if auth and auth.get("token"):
        token = auth["token"]
    # Fallback: Check if token is in query parameters
    else:
        query_string = environ.get('QUERY_STRING', '')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

    if not token:
        print(f"Client {sid} disconnected: No token provided")
        await sio.disconnect(sid)
        return

    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        if payload.get("type") != "access":
            print(f"Client {sid} disconnected: Invalid token type")
            await sio.disconnect(sid)
            return
        email = payload.get("sub")
        user = await users_collection.find_one({"email": email})
        if not user:
            print(f"Client {sid} disconnected: User not found")
            await sio.disconnect(sid)
            return
        await sio.save_session(sid, {"user": user})
        print(f"Client connected: {sid} (email: {email})")
        #await sio.emit('message', {'data': 'Connected to server!'}, to=sid)
        await sio.emit('Commander', {'type':"commander", "Status": "Started", 'response': f'Commander {user["name"]} initiate recording!'}, to=sid)
    except Exception as e:
        print(f"WebSocket auth error for client {sid}: {e}")
        await sio.disconnect(sid)

@sio.event
async def disconnect(sid):
    """Handle WebSocket disconnection"""
    print(f"Client disconnected: {sid}")

@sio.event
async def user_update(sid, data):
    """Handle WebSocket user update event"""
    session = await sio.get_session(sid)
    user = session["user"]
    try:
        name = data.get("name")
        if not name:
            await sio.emit('error', {'detail': 'Name is required'}, to=sid)
            return

        # Update user in MongoDB
        result = await users_collection.update_one(
            {"email": user["email"]},
            {"$set": {"name": name}},
            upsert=False
        )

        if result.modified_count:
            updated_user = await users_collection.find_one({"email": user["email"]})
            updated_user["id"] = str(updated_user["_id"])
            await sio.emit('user_updated', updated_user, to=sid)
        else:
            await sio.emit('error', {'detail': 'No changes made'}, to=sid)
    except Exception as e:
        await sio.emit('error', {'detail': str(e)}, to=sid)

@sio.event
async def message(sid, data):
    """Handle WebSocket message event"""
    try:
        data = json.loads(data)
        user_query = data.get("user_query", "")
        print(f"Message from {sid}: {data} | User query: {user_query}")
        
        # Call the async function that handles the agent processing
        await sio.emit('Agent', {'type':"Coordinator Agent", "Status": "Initiated", 'response': 'Coordinator Agent initiating the process.'}, to=sid)
        #result = await process_user_query_simple(user_query, sid)
        await process_user_query_simple(user_query, sid)
        #await sio.emit('message', {'detail': result}, to=sid) #not required here, handled in process_user_query_simple
        
    except Exception as e:
        print(f"Error in message handler: {e}")
        await sio.emit('message', {'detail': f'Error: {str(e)}'}, to=sid)

