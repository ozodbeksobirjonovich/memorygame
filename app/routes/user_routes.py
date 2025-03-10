from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user, get_password_hash, verify_password
from app.database import load_regions
from app.models import User
import os
from pathlib import Path
import shutil
from datetime import datetime

router = APIRouter(tags=["User"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/profile")
async def profile_page(request: Request, current_user: User = Depends(get_current_user)):
    regions = load_regions()
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user,
        "regions": regions
    })

@router.post("/update-profile")
async def update_profile(
    full_name: str = Form(None),
    current_password: str = Form(None),
    new_password: str = Form(None),
    region: str = Form(None),
    district: str = Form(None),
    avatar: UploadFile = File(None),
    current_user: User = Depends(get_current_user)
):
    update_data = {}
    
    # Update full name if provided
    if full_name:
        update_data["full_name"] = full_name
    
    # Update password if both current and new passwords are provided
    if current_password and new_password:
        if not verify_password(current_password, current_user.password):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Joriy parol noto'g'ri"}
            )
        
        update_data["password"] = get_password_hash(new_password)
    
    # Update region and district if provided
    if region:
        update_data["region"] = region
    
    if district:
        update_data["district"] = district
    
    # Update avatar if provided
    if avatar and avatar.filename:
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("app/static/uploads")
        if not uploads_dir.exists():
            uploads_dir.mkdir(parents=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(avatar.filename)[1]
        avatar_filename = f"{current_user.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"
        
        # Save file
        file_path = uploads_dir / avatar_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)
        
        update_data["avatar"] = avatar_filename
    
    # Update user if there are changes
    if update_data:
        try:
            query = User.update(**update_data).where(User.id == current_user.id)
            query.execute()
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"detail": "Profil muvaffaqiyatli yangilandi"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": f"Profilni yangilashda xatolik: {str(e)}"}
            )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Yangilanishlar topilmadi"}
    )

@router.get("/api/get-districts")
async def get_districts(region: str):
    regions = load_regions()
    
    if region in regions:
        return {"districts": regions[region]}
    
    return {"districts": []}