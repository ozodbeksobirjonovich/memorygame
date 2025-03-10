from datetime import datetime, timedelta
import secrets
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status
from app.models import User, Session
import uuid

# Security constants
SESSION_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username):
    try:
        return User.get(User.username == username)
    except User.DoesNotExist:
        return None

def authenticate_user(username, password):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_session(user):
    # Generate random session id
    session_id = str(uuid.uuid4())
    expiry = datetime.now() + timedelta(days=SESSION_EXPIRE_DAYS)
    
    # Delete any existing sessions for this user
    Session.delete().where(Session.user == user).execute()
    
    # Create new session
    session = Session.create(
        session_id=session_id,
        user=user,
        expiry=expiry
    )
    
    return session_id

def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        session = Session.get(Session.session_id == session_id)
        if not session.is_valid():
            # Delete expired session
            session.delete_instance()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )
        
        return session.user
    except Session.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )