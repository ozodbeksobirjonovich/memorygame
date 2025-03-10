from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user, get_password_hash
from app.database import get_db, load_regions
import aiosqlite
import os
from pathlib import Path
import shutil
from datetime import datetime

router = APIRouter(tags=["User"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/profile")
async def profile_page(request: Request, current_user = Depends(get_current_user)):
    regions = await load_regions()
    
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
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    user_id = current_user["id"]
    updates = {}
    
    # Update full name if provided
    if full_name:
        updates["full_name"] = full_name
    
    # Update password if both current and new passwords are provided
    if current_password and new_password:
        from app.auth import verify_password
        
        if not verify_password(current_password, current_user["password"]):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Current password is incorrect"}
            )
        
        updates["password"] = get_password_hash(new_password)
    
    # Update region and district if provided
    if region:
        updates["region"] = region
    
    if district:
        updates["district"] = district
    
    # Update avatar if provided
    if avatar and avatar.filename:
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("app/static/uploads")
        if not uploads_dir.exists():
            uploads_dir.mkdir(parents=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(avatar.filename)[1]
        avatar_filename = f"{current_user['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"
        
        # Save file
        file_path = uploads_dir / avatar_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)
        
        updates["avatar"] = avatar_filename
    
    # Construct and execute the update query
    if updates:
        query_parts = []
        query_values = []
        
        for key, value in updates.items():
            query_parts.append(f"{key} = ?")
            query_values.append(value)
        
        query_values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(query_parts)} WHERE id = ?"
        
        try:
            await db.execute(query, query_values)
            await db.commit()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"detail": "Profile updated successfully"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": f"Failed to update profile: {str(e)}"}
            )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "No updates provided"}
    )

@router.get("/api/get-districts")
async def get_districts(region: str):
    regions = await load_regions()
    
    if region in regions:
        return {"districts": regions[region]}
    
    return {"districts": []}