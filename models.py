from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    name: str
    email: EmailStr

class UserInDB(User):
    id: Optional[str] = None

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    name: str
    email: EmailStr
    otp: str

class OTPVerifyLogin(BaseModel):
    email: EmailStr
    otp: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    status: str


class SignupVerifyRequest(BaseModel):
    name: str
    email: EmailStr
    otp: str

class RefreshToken(BaseModel):
    refresh_token: str

class QueryRequest(BaseModel):
    user_query: str
    mode: str

class QueryResponse(BaseModel):
    status: str
    message: str