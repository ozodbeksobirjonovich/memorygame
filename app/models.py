from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    birthdate: date
    region: str
    district: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class GameResult(BaseModel):
    user_id: int
    score: int
    level: int
    stage: int
    grid_size: int
    duration: int
    completed: bool

class UserProfile(BaseModel):
    id: int
    username: str
    full_name: str
    birthdate: date
    region: str
    district: str
    avatar: str
    created_at: datetime