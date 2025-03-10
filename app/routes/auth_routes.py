from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from app.auth import authenticate_user, create_access_token, get_current_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db, load_regions
import aiosqlite
import os
from pathlib import Path
import shutil

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register")
async def register_page(request: Request):
    regions = await load_regions()
    return templates.TemplateResponse("register.html", {
        "request": request,
        "regions": regions
    })

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_id": user["id"]}

@router.post("/register")
async def register_user(
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    birthdate: str = Form(...),
    region: str = Form(...),
    district: str = Form(...),
    avatar: UploadFile = File(None),
    db = Depends(get_db)
):
    # Check if username already exists
    async with db.execute("SELECT username FROM users WHERE username = ?", (username,)) as cursor:
        existing_user = await cursor.fetchone()
        if existing_user:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Username already registered"}
            )
    
    # Hash the password
    hashed_password = get_password_hash(password)
    
    # Save avatar if provided
    avatar_filename = "default_avatar.png"
    if avatar and avatar.filename:
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("app/static/uploads")
        if not uploads_dir.exists():
            uploads_dir.mkdir(parents=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(avatar.filename)[1]
        avatar_filename = f"{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"
        
        # Save file
        file_path = uploads_dir / avatar_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)
    
    # Insert user into database
    try:
        await db.execute("""
        INSERT INTO users (username, password, full_name, birthdate, region, district, avatar)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, hashed_password, full_name, birthdate, region, district, avatar_filename))
        await db.commit()
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"detail": "User registered successfully"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Registration failed: {str(e)}"}
        )