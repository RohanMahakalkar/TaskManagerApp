from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TaskCreate(BaseModel):
    name: str

class TaskUpdate(BaseModel):
    name: Optional[str] = None

class TaskOut(BaseModel):
    id: str
    name: str
    user_id: str
    created_at: datetime
    updated_at: datetime

