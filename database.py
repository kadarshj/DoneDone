from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()


# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI")  # Replace with your MongoDB URI
DB_NAME = os.getenv("DB_NAME")

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_URI, server_api=ServerApi('1'))
db = client[DB_NAME]

# Collections
users_collection = db["users"]
otp_collection = db["otps"]
User_query_collection = db["user_queries"]
#user_contacts_collection = db["user_contacts"]
read_contacts_collection = db["read_contacts"]
schedule_call_reminder_collection = db["schedule_call_reminders"]
update_health_metrics_collection = db["update_health_metrics"]
set_health_reminder_collection = db["set_health_reminders"]
send_mood_history_collection = db["send_mood_history"]
aggregate_tasks_collection = db["aggregate_tasks"]
store_client_insights_collection = db["store_client_insights"]
store_meeting_summary_collection = db["store_meeting_summary"]

async def ping_server():
    """Test MongoDB connection"""
    try:
        await client.admin.command('ping')
        print("Pinged your deployment. Successfully connected to MongoDB!")
        # Create index for OTP collection (expire after 5 minutes)
        await otp_collection.create_index("created_at", expireAfterSeconds=300)
        # Create unique index for user email
        await users_collection.create_index("email", unique=True)
    except Exception as e:
        print(f"Connection error: {e}")