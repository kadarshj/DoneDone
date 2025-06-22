from google.adk.agents import LlmAgent
from google.genai import types
from SocketCreate import sio
import os
from dotenv import load_dotenv

from agents.journal_prompt import journal_agent_instruction

# Imports to send email
import smtplib
from email.message import EmailMessage

# Imports to get current date, time and day
from datetime import datetime

# Imports to schedule emails
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

MODEL = "gemini-2.5-flash-preview-05-20"

scheduler = AsyncIOScheduler()

# Schedules a one-time reminder job
def schedule_reminder(reminder_time: str, recipient_email: str, subject: str, content: str) -> dict:
    """
    Schedules a one-time email reminder job for the given time.

    Args:
        reminder_time (str): The datetime 30 minutes before the task is due.
        recipient_email (str): The email address of the recipient.
        subject (str): The subject line of the email.
        content (str): The content of the email.

    Returns: dict: A dictionary containing the result.
        Includes a 'status' key ('success' or 'error' or 'warning').
        If 'success', includes a 'success_message' key.
        If 'warning', includes a 'warning_message' key.
        If 'error', includes an 'error_message' key.
    """
    print("---------Called tool schedule_reminder---------")

    try:
        reminder_time_dt = datetime.fromisoformat(reminder_time)
    except ValueError:
        return {"status": "error", "error_message": "Invalid datetime format. Please use YYYY-MM-DDTHH:MM:SS"}

    print(f"Reminder Time: {reminder_time_dt} \n Email: {recipient_email} \n Subject: {subject} \n Content: {content}")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if reminder_time_dt <= datetime.now():
        return {"status": "warning", "warning_message": f"Reminder skipped — time has passed."}
    
    scheduler.add_job(
        send_email,
        trigger='date',
        run_date=reminder_time_dt,
        args=[recipient_email,subject,content]
    )
    return {"status": "success", "success_message": f"Reminder scheduled at {reminder_time_dt.strftime('%Y-%m-%d %H:%M:%S')}"}

def get_date():
    """
    Returns current date, time, and day of the week in string format.
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    day_of_week = now.strftime("%A")
    return f"{date_str} ({day_of_week})"

def send_email(recipient_email: str, subject: str, content: str) -> dict:
    """
    Sends an email to the user.

    Args:
        recipient_email (str): The email address of the recipient.
        subject (str): The subject line of the email.
        content (str): The content of the email.

    Returns: dict: A dictionary containing the result.
        Includes a 'status' key ('success' or 'error').
        If 'success', includes a 'success_message' key.
        If 'error', includes an 'error_message' key.
    """
    sender_email = os.getenv("EMAIL_HOST_USER")
    sender_password = os.getenv("EMAIL_HOST_PASSWORD")
    print("-----------Using tool to send email-----------")
    if not sender_email or not sender_password:
        print("-----------Email credentials not found-----------")
        return {"status": "error", "error_message": f"Sorry, I don't have email credentials."}
    
    # --- Create the Email Message ---
    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    email_body = ""
    # Format the to-do list for the email body
    if not content:
        email_body += "No items on the list today. Great job!\n"
    else:
        email_body += content

    msg.set_content(email_body)

    # --- Send the Email ---
    try:
        print("-----------Trying to send email-----------")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        return {"status": "success", "success_message": "Email sent successfully."}
    except smtplib.SMTPAuthenticationError as e:
        print("-----------Unable to login-----------")
        return {"status": "error", "error_message": f"Unable to login. Make sure 2FA is enabled."}
    except Exception as e:
        print("-----------Some error occurred-----------")
        return {"status": "error", "error_message": e}

# Journal agent
# It uses three tools:
# send_email - send to do list and reminders to users.
# get_date - get today's date, current time, and day of the week.
# schedule_reminder - schedule a send_email task using AsycnIOScheduler.
journal_agent = LlmAgent(
    model=MODEL,
    name="journal_agent",
    description="An intelligent personal journal assistant that helps users summarize daily journal entries, generate actionable to-do lists, email them with schedule details, and set task reminders automatically.",
    instruction=journal_agent_instruction,
    tools=[send_email,get_date,schedule_reminder],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2, # More deterministic output
    )
)