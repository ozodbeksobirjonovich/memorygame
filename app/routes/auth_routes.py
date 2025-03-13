# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import Response
from app.auth import authenticate_user, create_session, get_current_user, get_password_hash
from app.database import load_regions
from app.models import User
import os
from pathlib import Path
import shutil
from datetime import datetime

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register")
async def register_page(request: Request):
    regions = load_regions()
    return templates.TemplateResponse("register.html", {
        "request": request,
        "regions": regions
    })

@router.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    user = authenticate_user(username, password)
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Noto'g'ri foydalanuvchi nomi yoki parol"}
        )
    
    # Create session
    session_id = create_session(user)
    
    # Set cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=60*60*24*7,  # 7 days
        path="/",
    )
    
    # Check if admin and return appropriate redirect
    if user.is_admin:
        return {"status": "success", "user_id": user.id, "is_admin": True}
    else:
        return {"status": "success", "user_id": user.id, "is_admin": False}

@router.post("/register")
async def register_user(
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    birthdate: str = Form(...),
    region: str = Form(...),
    district: str = Form(...),
    avatar: UploadFile = File(None)
):
    # Check if username already exists
    user_exists = User.select().where(User.username == username).exists()
    if user_exists:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Bu foydalanuvchi nomi allaqachon ro'yxatga olingan"}
        )
    
    # Hash the password
    hashed_password = get_password_hash(password)
    
    # Save avatar if provided, else use default
    avatar_filename = "default_avatar.jpg"
    
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
    
    # Create user
    try:
        # Set first user as admin
        is_admin = False
        if User.select().count() == 0:
            is_admin = True
            
        User.create(
            username=username,
            password=hashed_password,
            full_name=full_name,
            birthdate=birthdate,
            region=region,
            district=district,
            avatar=avatar_filename,
            is_admin=is_admin,
            coins=10  # Starting coins
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"detail": "Foydalanuvchi muvaffaqiyatli ro'yxatga olindi"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Ro'yxatdan o'tishda xatolik: {str(e)}"}
        )

@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie(key="session_id")
    return RedirectResponse(url="/login")