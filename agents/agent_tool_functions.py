from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiosmtplib import SMTP, SMTPException
import spacy
from textblob import TextBlob
import jinja2
from datetime import datetime, timezone
import os
import re
import pymongo.errors
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bson import ObjectId
from pydantic import BaseModel, Field
from database import (
    read_contacts_collection,
    schedule_call_reminder_collection,
    update_health_metrics_collection,
    set_health_reminder_collection,
    send_mood_history_collection,
    aggregate_tasks_collection,
    store_client_insights_collection,
    store_meeting_summary_collection,
    users_collection
)

# Pydantic models
class HealthMetrics(BaseModel):
    bmi: Optional[float] = Field(None, description="Body Mass Index")
    steps: Optional[int] = Field(None, description="Daily step count")

class TimeRange(BaseModel):
    start: str = Field(..., description="Start date in ISO format, e.g., 2025-06-01T00:00:00Z")
    end: str = Field(..., description="End date in ISO format, e.g., 2025-06-24T23:59:59Z")

class Task(BaseModel):
    agent: str = Field(..., description="Agent responsible for the task")
    description: Optional[str] = Field(None, description="Task description")
    timestamp: Optional[str] = Field(None, description="Task timestamp in ISO format")

class Tasks(BaseModel):
    tasks: List[Task] = Field(..., description="List of tasks")

class ClientInsights(BaseModel):
    objectives: List[str] = Field(..., description="List of client objectives")
    pain_points: List[str] = Field(..., description="List of client pain points")
    goals: List[str] = Field(..., description="List of client goals")

class MeetingSummary(BaseModel):
    topics: List[str] = Field(..., description="List of meeting topics")
    action_items: List[str] = Field(..., description="List of action items")
    outcomes: List[str] = Field(..., description="List of outcomes")

class Deal(BaseModel):
    item: str = Field(..., description="Item name")
    price: float = Field(..., description="Price of the item")
    source: str = Field(..., description="Source of the deal")
    url: str = Field(..., description="URL to the deal")

# SMTP Configuration from environment variables
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"

# External scheduler instance
scheduler = AsyncIOScheduler()

async def get_user_email(user_id: str) -> str:
    """
    Fetch user email from users_collection using _id.
    Inputs: user ID (ObjectId string)
    Outputs: User email or default if not found
    """
    try:
        user = await users_collection.find_one({"_id": ObjectId(user_id)}, {"email": 1})
        print(f"User found: {user}")
        if not user or "email" not in user:
            raise ValueError(f"No email found for user_id: {user_id}")
        return user["email"]
    except pymongo.errors.PyMongoError as e:
        print(f"MongoDB error in get_user_email: {str(e)}")
        return "default@example.com"
    except Exception as e:
        print(f"Error in get_user_email: {str(e)}")
        return "default@example.com"

# SocialLifeAgent Tools
async def read_contacts(user_id: str) -> List[dict]:
    """
    Fetch contacts from MongoDB for a user.
    Inputs: user ID
    Outputs: List of contacts (name, phone, email)
    """
    try:
        cursor = read_contacts_collection.find({"user_id": user_id}, {"name": 1, "phone": 1, "email": 1, "_id": 0})
        contacts = await cursor.to_list(length=None)
        return contacts
    except pymongo.errors.PyMongoError as e:
        print(f"MongoDB error in read_contacts: {str(e)}")
        return []
    except Exception as e:
        print(f"Error in read_contacts: {str(e)}")
        return []

async def schedule_call_reminder(user_id: str, contact_name: str, phone: str, reminder_time: str) -> dict:
    """
    Store a call reminder in MongoDB and schedule an email reminder.
    Inputs: user ID, contact name, phone, reminder time (ISO format)
    Outputs: Confirmation with reminder ID
    """
    try:
        reminder = {
            "user_id": user_id,
            "contact_name": contact_name,
            "phone": phone,
            "reminder_time": reminder_time,
            "created_at": datetime.now(timezone.utc)
        }
        result = await schedule_call_reminder_collection.insert_one(reminder)
        
        reminder_dt = datetime.fromisoformat(reminder_time.replace("Z", "+00:00"))
        recipient_email = await get_user_email(user_id)
        subject = f"Reminder: Call {contact_name}"
        message = f"Don't forget to call {contact_name} at {phone} on {reminder_dt}."
        scheduler.add_job(
            send_followup_email,
            'date',
            run_date=reminder_dt,
            args=[recipient_email, subject, message],
            id=f"call_reminder_{str(result.inserted_id)}"
        )
        
        return {"status": "success", "reminder_id": str(result.inserted_id)}
    except pymongo.errors.PyMongoError as e:
        print(f"MongoDB error in schedule_call_reminder: {str(e)}")
        return {"status": "error", "message": str(e)}
    except ValueError as e:
        print(f"Value error in schedule_call_reminder: {str(e)}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Error in schedule_call_reminder: {str(e)}")
        return {"status": "error", "message": str(e)}

async def send_followup_email(recipient_email: str, subject: str, message: str) -> dict:
    """
    Send a follow-up email using configured SMTP.
    Inputs: Recipient email, subject, message content
    Outputs: Confirmation of sent email
    """
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = "noreply@aminobots.com"
        msg["To"] = recipient_email
        msg.attach(MIMEText(message, "plain"))

        async with SMTP(hostname=EMAIL_HOST, port=EMAIL_PORT, use_tls=EMAIL_USE_TLS) as server:
            await server.login(EMAIL_USER, EMAIL_PASSWORD)
            await server.send_message(msg)
        return {"status": "sent", "recipient": recipient_email}
    except SMTPException as e:
        print(f"SMTP error in send_followup_email: {str(e)}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Error in send_followup_email: {str(e)}")
        return {"status": "error", "message": str(e)}

# HealthTrackerAgent Tools
async def update_health_metrics(user_id: str, metrics: HealthMetrics) -> dict:
    """
    Store health metrics in MongoDB.
    Inputs: user ID, metrics (HealthMetrics instance)
    Outputs: Confirmation of update
    """
    try:
        health_data = {
            "user_id": user_id,
            "metrics": metrics.dict(exclude_none=True),
            "timestamp": datetime.now(timezone.utc)
        }
        result = await update_health_metrics_collection.insert_one(health_data)
        return {"status": "success", "entry_id": str(result.inserted_id)}
    except pymongo.errors.PyMongoError as e:
        print(f"MongoDB error in update_health_metrics: {str(e)}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Error in update_health_metrics: {str(e)}")
        return {"status": "error", "message": str(e)}

async def set_health_reminder(user_id: str, event_title: str, event_time: str) -> dict:
    """
    Store a health reminder in MongoDB and schedule an email reminder.
    Inputs: user_id, event title (e.g., "Workout"), event time (ISO format)
    Outputs: Confirmation with event ID
    """
    try:
        reminder = {
            "user_id": user_id,
            "event_title": event_title,
            "event_time": event_time,
            "created_at": datetime.now(timezone.utc)
        }
        result = await set_health_reminder_collection.insert_one(reminder)
        
        reminder_dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
        recipient_email = await get_user_email(user_id)
        subject = f"Health Reminder: {event_title}"
        message = f"Reminder: {event_title} scheduled for {reminder_dt}."
        scheduler.add_job(
            send_followup_email,
            'date',
            run_date=reminder_dt,
            args=[recipient_email, subject, message],
            id=f"health_reminder_{str(result.inserted_id)}"
        )
        
        return {"status": "success", "event_id": str(result.inserted_id)}
    except pymongo.errors.PyMongoError as e:
        print(f"MongoDB error in set_health_reminder: {str(e)}")
        return {"status": "error", "message": str(e)}
    except ValueError as e:
        print(f"Value error in set_health_reminder: {str(e)}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Error in set_health_reminder: {str(e)}")
        return {"status": "error", "message": str(e)}

async def send_progress_email(user_id: str, time_range: TimeRange) -> dict:
    """
    Send a health progress email based on MongoDB data using configured SMTP.
    Inputs: user ID, time range (TimeRange instance)
    Outputs: Confirmation with recipient email
    """
    try:
        start = datetime.fromisoformat(time_range.start.replace("Z", "+00:00"))
        end = datetime.fromisoformat(time_range.end.replace("Z", "+00:00"))
        cursor = update_health_metrics_collection.find({
            "user_id": user_id,
            "timestamp": {"$gte": start, "$lte": end}
        })
        metrics_list = await cursor.to_list(length=None)
        summary = f"Health Progress from {start.date()} to {end.date()}:\n"
        for entry in metrics_list:
            summary += f"- {entry['timestamp'].date()}: {entry.get('metrics', {})}\n"
        
        msg = MIMEMultipart()
        msg["Subject"] = "Your Health Progress Report"
        msg["From"] = "noreply@aminobots.com"
        recipient_email = await get_user_email(user_id)
        msg["To"] = recipient_email
        msg.attach(MIMEText(summary, "plain"))

        async with SMTP(hostname=EMAIL_HOST, port=EMAIL_PORT, use_tls=EMAIL_USE_TLS) as server:
            await server.login(EMAIL_USER, EMAIL_PASSWORD)
            await server.send_message(msg)
        return {"status": "sent", "recipient": recipient_email}
    except pymongo.errors.PyMongoError as e:
        print(f"MongoDB error in send_progress_email: {str(e)}")
        return {"status": "error", "message": str(e)}
    except SMTPException as e:
        print(f"SMTP error in send_progress_email: {str(e)}")
        return {"status": "error", "message": str(e)}
    except ValueError as e:
        print(f"Value error in send_progress_email: {str(e)}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Error in send_progress_email: {str(e)}")
        return {"status": "error", "message": str(e)}

# SmartShopperAgent Tools
def parse_transcript(transcript: str) -> List[str]:
    """
    Extract shopping items from a transcript using regex.
    Inputs: Text transcript
    Outputs: List of identified items
    """
    try:
        pattern = r"\b(laptop|phone|jeans|shirt|shoes|headphones)\b"
        items = re.findall(pattern, transcript.lower())
        return list(set(items))
    except Exception as e:
        print(f"Error in parse_transcript: {str(e)}")
        return []

def find_deals(items: List[str], max_results: int) -> List[Deal]:
    """
    Find deals for items using a mock API (replace with real e-commerce API).
    Inputs: List of items, max results per item
    Outputs: List of deals with name, price, source, URL
    """
    try:
        deals = []
        for item in items:
            for i in range(max_results):
                deals.append(Deal(
                    item=item,
                    price=100.0 + i * 10,
                    source=f"MockStore{i+1}",
                    url=f"https://mockstore.com/{item}/{i+1}"
                ))
        return deals
    except Exception as e:
        print(f"Error in find_deals: {str(e)}")
        return []

def compare_deals(deals: List[Deal]) -> str:
    
    """
    Ascendingly:
    Generate a comparison table for deals.
    Inputs: List of deals (Deal instances)
    Outputs: Markdown table as string
    """
    try:
        template = jinja2.Template("""
| Item | Price | Source | URL |
|------|-------|--------|-----|
{% for deal in deals %}
| {{ deal.item }} | ${{ deal.price }} | {{ deal.source }} | [Link]({{ deal.url }}) |
{% endfor %}
        """)
        return template.render(deals=deals)
    except jinja2.TemplateError as e:
        print(f"Template error in compare_deals: {str(e)}")
        return ""
    except Exception as e:
        print(f"Error in compare_deals: {str(e)}")
        return ""

# MoodInsightAgent Tools
def detect_mood(text: str) -> dict:
    """
    Detect mood from text using TextBlob.
    Inputs: User text input
    Outputs: Mood score and sentiment
    """
    try:
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        mood = "neutral"
        if sentiment > 0.2:
            mood = "positive"
        elif sentiment < -0.2:
            mood = "negative"
        return {"mood": mood, "score": sentiment}
    except Exception as e:
        print(f"Error in detect_mood: {str(e)}")
        return {"mood": "neutral", "score": 0.0}

def suggest_content(mood: str) -> List[dict]:
    """
    Suggest motivational content based on mood.
    Inputs: Mood (positive, neutral, negative)
    Outputs: List of content (title, URL)
    """
    try:
        content_map = {
            "negative": [
                {"title": "Motivational Speech", "url": "https://youtube.com/motivation1"},
                {"title": "Uplifting Music", "url": "https://youtube.com/music1"}
            ],
            "neutral": [
                {"title": "Productivity Tips", "url": "https://youtube.com/tips1"}
            ],
            "positive": [
                {"title": "Success Stories", "url": "https://youtube.com/stories1"}
            ]
        }
        return content_map.get(mood, [])
    except Exception as e:
        print(f"Error in suggest_content: {str(e)}")
        return []

async def send_mood_summary_email(user_id: str, time_range: TimeRange) -> dict:
    """
    Send a mood summary email based on MongoDB data using configured SMTP.
    Inputs: user ID, time range (TimeRange instance)
    Outputs: Confirmation with recipient email
    """
    try:
        start = datetime.fromisoformat(time_range.start.replace("Z", "+00:00"))
        end = datetime.fromisoformat(time_range.end.replace("Z", "+00:00"))
        cursor = send_mood_history_collection.find({
            "user_id": user_id,
            "timestamp": {"$gte": start, "$lte": end}
        })
        moods_list = await cursor.to_list(length=None)
        summary = f"Mood Summary from {start.date()} to {end.date()}:\n"
        for entry in moods_list:
            summary += f"- {entry['timestamp'].date()}: {entry['mood']}\n"
        
        msg = MIMEMultipart()
        msg["Subject"] = "Your Mood Summary Report"
        msg["From"] = "noreply@aminobots.com"
        recipient_email = await get_user_email(user_id)
        msg["To"] = recipient_email
        msg.attach(MIMEText(summary, "plain"))

        async with SMTP(hostname=EMAIL_HOST, port=EMAIL_PORT, use_tls=EMAIL_USE_TLS) as server:
            await server.login(EMAIL_USER, EMAIL_PASSWORD)
            await server.send_message(msg)
        return {"status": "sent", "recipient": recipient_email}
    except pymongo.errors.PyMongoError as e:
        print(f"MongoDB error in send_mood_summary_email: {str(e)}")
        return {"status": "error", "message": str(e)}
    except SMTPException as e:
        print(f"SMTP error in send_mood_summary_email: {str(e)}")
        return {"status": "error", "message": str(e)}
    except ValueError as e:
        print(f"Value error in send_mood_summary_email: {str(e)}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Error in send_mood_summary_email: {str(e)}")
        return {"status": "error", "message": str(e)}

# CoordinatorAgent Tools
async def aggregate_tasks(user_id: str, date: str) -> Tasks:
    """
    Aggregate tasks from all agents for a user on a specific date.
    Inputs: user ID, date (ISO format, e.g., "2025-06-24")
    Outputs: Aggregated task data
    """
    try:
        start = datetime.fromisoformat(date.replace("Z", "+00:00"))
        end = start.replace(hour=23, minute=59, second=59)
        cursor = aggregate_tasks_collection.find({
            "user_id": user_id,
            "timestamp": {"$gte": start, "$lte": end}
        })
        tasks = await cursor.to_list(length=None)
        return Tasks(tasks=[Task(**task) for task in tasks])
    except pymongo.errors.PyMongoError as e:
        print(f"MongoDB error in aggregate_tasks: {str(e)}")
        return Tasks(tasks=[])
    except ValueError as e:
        print(f"Value error in aggregate_tasks: {str(e)}")
        return Tasks(tasks=[])
    except Exception as e:
        print(f"Error in aggregate_tasks: {str(e)}")
        return Tasks(tasks=[])

def compile_report(tasks: Tasks) -> str:
    """
    Compile a daily report from aggregated tasks.
    Inputs: Aggregated task data (Tasks instance)
    Outputs: Markdown report
    """
    try:
        template = jinja2.Template("""
# Daily Report for {{ date }}
{% for task in tasks %}
- **Agent**: {{ task.agent }}
- **Task**: {{ task.description }}
- **Timestamp**: {{ task.timestamp }}
{% endfor %}
        """)
        return template.render(tasks=tasks.tasks, date=datetime.now(timezone.utc).date())
    except jinja2.TemplateError as e:
        print(f"Template error in compile_report: {str(e)}")
        return ""
    except Exception as e:
        print(f"Error in compile_report: {str(e)}")
        return ""

async def send_report_email(report: str, recipient_email: str) -> dict:
    """
    Send the daily report via email using configured SMTP.
    Inputs: Report content, recipient email
    Outputs: Confirmation of sent email
    """
    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"Daily Report - {datetime.now(timezone.utc).date()}"
        msg["From"] = "noreply@aminobots.com"
        msg["To"] = recipient_email
        msg.attach(MIMEText(report, "plain"))

        async with SMTP(hostname=EMAIL_HOST, port=EMAIL_PORT, use_tls=EMAIL_USE_TLS) as server:
            await server.login(EMAIL_USER, EMAIL_PASSWORD)
            await server.send_message(msg)
        return {"status": "sent", "recipient": recipient_email}
    except SMTPException as e:
        print(f"SMTP error in send_report_email: {str(e)}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Error in send_report_email: {str(e)}")
        return {"status": "error", "message": str(e)}

# ClientIntelAgent Tools
def parse_client_transcript(transcript: str) -> ClientInsights:
    """
    Extract objectives, pain points, and goals from client transcript.
    Inputs: Client transcript text
    Outputs: Structured insights
    """
    try:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(transcript)
        objectives = [sent.text for sent in doc.sents if "objective" in sent.text.lower()]
        pain_points = [sent.text for sent in doc.sents if "problem" in sent.text.lower() or "issue" in sent.text.lower()]
        goals = [sent.text for sent in doc.sents if "goal" in sent.text.lower()]
        return ClientInsights(objectives=objectives, pain_points=pain_points, goals=goals)
    except Exception as e:
        print(f"Error in parse_client_transcript: {str(e)}")
        return ClientInsights(objectives=[], pain_points=[], goals=[])

async def store_client_insights(user_id: str, insights: ClientInsights) -> dict:
    """
    Store client insights in MongoDB.
    Inputs: user ID, insights (ClientInsights instance)
    Outputs: Confirmation with entry ID
    """
    try:
        insight_data = {
            "user_id": user_id,
            "insights": insights.dict(),
            "timestamp": datetime.now(timezone.utc)
        }
        result = await store_client_insights_collection.insert_one(insight_data)
        return {"status": "success", "entry_id": str(result.inserted_id)}
    except pymongo.errors.PyMongoError as e:
        print(f"MongoDB error in store_client_insights: {str(e)}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Error in store_client_insights: {str(e)}")
        return {"status": "error", "message": str(e)}

# ProposalDraftingAgent Tools
async def retrieve_client_insights(user_id: str, client_id: str) -> ClientInsights:
    """
    Retrieve client insights from MongoDB.
    Inputs: user ID, client_id
    Outputs: Insights data
    """
    try:
        insight = await store_client_insights_collection.find_one({"user_id": user_id, "client_id": client_id})
        if insight and "insights" in insight:
            return ClientInsights(**insight["insights"])
        return ClientInsights(objectives=[], pain_points=[], goals=[])
    except pymongo.errors.PyMongoError as e:
        print(f"MongoDB error in retrieve_client_insights: {str(e)}")
        return ClientInsights(objectives=[], pain_points=[], goals=[])
    except Exception as e:
        print(f"Error in retrieve_client_insights: {str(e)}")
        return ClientInsights(objectives=[], pain_points=[], goals=[])

def generate_proposal(insights: ClientInsights) -> str:
    """
    Generate a structured proposal from client insights.
    Inputs: Insights (ClientInsights instance)
    Outputs: Markdown proposal
    """
    try:
        template = jinja2.Template("""
# Proposal

## Objectives
{% for obj in insights.objectives %}
- {{ obj }}
{% endfor %}

## Challenges
{% for pain in insights.pain_points %}
- {{ pain }}
{% endfor %}

## Solutions
{% for goal in insights.goals %}
- {{ goal }}
{% endfor %}
        """)
        return template.render(insights=insights)
    except jinja2.TemplateError as e:
        print(f"Template error in generate_proposal: {str(e)}")
        return ""
    except Exception as e:
        print(f"Error in generate_proposal: {str(e)}")
        return ""

async def send_proposal_email(proposal: str, recipient_email: str) -> dict:
    """
    Send the proposal via email using configured SMTP.
    Inputs: Proposal content, recipient email
    Outputs: Confirmation of sent email
    """
    try:
        msg = MIMEMultipart()
        msg["Subject"] = "Client Proposal"
        msg["From"] = "noreply@aminobots.com"
        msg["To"] = recipient_email
        msg.attach(MIMEText(proposal, "plain"))

        async with SMTP(hostname=EMAIL_HOST, port=EMAIL_PORT, use_tls=EMAIL_USE_TLS) as server:
            await server.login(EMAIL_USER, EMAIL_PASSWORD)
            await server.send_message(msg)
        return {"status": "sent", "recipient": recipient_email}
    except SMTPException as e:
        print(f"SMTP error in send_proposal_email: {str(e)}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Error in send_proposal_email: {str(e)}")
        return {"status": "error", "message": str(e)}

# MeetingSummarizerAgent Tools
def parse_meeting_notes(notes: str) -> MeetingSummary:
    """
    Extract topics, action items, and outcomes from meeting notes.
    Inputs: Meeting notes text
    Outputs: Structured summary
    """
    try:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(notes)
        topics = [sent.text for sent in doc.sents if "topic" in sent.text.lower()]
        action_items = [sent.text for sent in doc.sents if "action" in sent.text.lower()]
        outcomes = [sent.text for sent in doc.sents if "outcome" in sent.text.lower()]
        return MeetingSummary(topics=topics, action_items=action_items, outcomes=outcomes)
    except Exception as e:
        print(f"Error in parse_meeting_notes: {str(e)}")
        return MeetingSummary(topics=[" "], action_items=[" "], outcomes=[" "])

def generate_meeting_summary(parsed_data: MeetingSummary) -> str:
    """
    Generate a meeting summary from parsed data.
    Inputs: Parsed meeting data (MeetingSummary instance)
    Outputs: Markdown summary
    """
    try:
        template = jinja2.Template("""
# Meeting Summary

## Topics
{% for topic in data.topics %}
- {{ topic }}
{% endfor %}

## Action Items
{% for action in data.action_items %}
- {{ action }}
{% endfor %}

## Outcomes
{% for outcome in data.outcomes %}
- {{ outcome }}
{% endfor %}
        """)
        return template.render(data=parsed_data)
    except jinja2.TemplateError as e:
        print(f"Template error in generate_meeting_summary: {str(e)}")
        return ""
    except Exception as e:
        print(f"Error in generate_meeting_summary: {str(e)}")
        return ""

async def store_meeting_summary(user_id: str, summary: MeetingSummary) -> dict:
    """
    Store meeting summary in MongoDB.
    Inputs: user ID, summary data (MeetingSummary instance)
    Outputs: Confirmation with entry ID
    """
    try:
        summary_data = {
            "user_id": user_id,
            "summary": summary.dict(),
            "timestamp": datetime.now(timezone.utc)
        }
        result = await store_meeting_summary_collection.insert_one(summary_data)
        return {"status": "success", "entry_id": str(result.inserted_id)}
    except pymongo.errors.PyMongoError as e:
        print(f"MongoDB error in store_meeting_summary: {str(e)}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Error in store_meeting_summary: {str(e)}")
        return {"status": "error", "message": str(e)}