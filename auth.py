import os
import random
import string
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from aiosmtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import users_collection, otp_collection

# Load environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/verify-otp")

async def send_otp_email(email: str, otp: str):
    """Send OTP email with professional template"""
    with open("templates/otp_email.html", "r") as file:
        html_content = file.read().replace("{{OTP}}", otp)

    msg = MIMEMultipart()
    msg["Subject"] = "Your OTP Code"
    msg["From"] = "noreply@aminobots.com"
    msg["To"] = email

    msg.attach(MIMEText(html_content, "html"))

    async with SMTP(hostname=EMAIL_HOST, port=EMAIL_PORT, use_tls=EMAIL_USE_TLS) as server:
        await server.login(EMAIL_USER, EMAIL_PASSWORD)
        await server.send_message(msg)

async def generate_otp(email: str, purpose: str = "login"):
    """Generate and store OTP with purpose (login or signup)"""
    otp = ''.join(random.choices(string.digits, k=6))
    await otp_collection.insert_one({
        "email": email,
        "otp": otp,
        "purpose": purpose,
        "created_at": datetime.utcnow()
    })
    await send_otp_email(email, otp)
    return otp

async def verify_otp(email: str, otp: str, purpose: str = "login"):
    """Verify OTP for specific purpose"""
    otp_doc = await otp_collection.find_one({"email": email, "otp": otp, "purpose": purpose})
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    # Delete OTP after verification
    await otp_collection.delete_one({"email": email, "otp": otp, "purpose": purpose})
    return True

async def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Verify JWT access token and get current user"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await users_collection.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        user["id"] = str(user["_id"])
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def refresh_access_token(refresh_token: str):
    """Generate new access token using refresh token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await users_collection.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return await create_access_token({"sub": email})
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")