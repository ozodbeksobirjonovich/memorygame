# app/routes/admin_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Query
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from app.auth import get_current_user, get_password_hash
from app.models import User, GameResult
from peewee import fn
from datetime import datetime

router = APIRouter(tags=["Admin"])
templates = Jinja2Templates(directory="app/templates")

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.get("/admin")
async def admin_dashboard(request: Request, admin_user: User = Depends(get_admin_user)):
    user_count = User.select().count()
    game_count = GameResult.select().count()
    
    # Get top users
    top_users = (GameResult
                .select(GameResult, User)
                .join(User)
                .group_by(GameResult.user)
                .having(GameResult.score == fn.MAX(GameResult.score))
                .order_by(GameResult.score.desc())
                .limit(5))
    
    top_users_data = []
    for result in top_users:
        top_users_data.append({
            'user_id': result.user.id,
            'username': result.user.username,
            'full_name': result.user.full_name,
            'score': result.score,
            'coins': result.user.coins
        })
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "user": admin_user,
        "user_count": user_count,
        "game_count": game_count,
        "top_users": top_users_data
    })

@router.get("/admin/users")
async def admin_users(
    request: Request, 
    search: Optional[str] = Query(None),
    admin_user: User = Depends(get_admin_user)
):
    query = User.select()
    
    if search and search.strip():
        query = query.where(
            (User.username.contains(search)) | 
            (User.full_name.contains(search)) |
            (User.region.contains(search))
        )
    
    users = []
    for user in query:
        users.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'region': user.region,
            'district': user.district,
            'birthdate': user.birthdate,
            'is_admin': user.is_admin,
            'coins': user.coins,
            'created_at': user.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "user": admin_user,
        "users": users,
        "search": search
    })

@router.get("/admin/user/{user_id}")
async def admin_user_edit(
    request: Request,
    user_id: int,
    admin_user: User = Depends(get_admin_user)
):
    try:
        edit_user = User.get_by_id(user_id)
        return templates.TemplateResponse("admin/user_edit.html", {
            "request": request,
            "user": admin_user,
            "edit_user": edit_user
        })
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

@router.post("/admin/user/{user_id}")
async def admin_user_update(
    user_id: int,
    full_name: str = Form(None),
    coins: int = Form(None),
    is_admin: bool = Form(False),
    new_password: str = Form(None),
    admin_user: User = Depends(get_admin_user)
):
    try:
        edit_user = User.get_by_id(user_id)
        
        # Update user data
        if full_name:
            edit_user.full_name = full_name
        
        if coins is not None:
            edit_user.coins = coins
        
        edit_user.is_admin = is_admin
        
        if new_password:
            edit_user.password = get_password_hash(new_password)
        
        edit_user.save()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": "User updated successfully"}
        )
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/admin/user/{user_id}")
async def admin_user_delete(
    user_id: int,
    admin_user: User = Depends(get_admin_user)
):
    try:
        if int(user_id) == admin_user.id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "You cannot delete your own account"}
            )
            
        edit_user = User.get_by_id(user_id)
        
        # Delete user and all related data
        edit_user.delete_instance(recursive=True)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": "User deleted successfully"}
        )
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

@router.get("/admin/results")
async def admin_results(
    request: Request,
    search: Optional[str] = Query(None),
    admin_user: User = Depends(get_admin_user)
):
    query = (GameResult
            .select(GameResult, User)
            .join(User))
    
    if search and search.strip():
        query = query.where(User.full_name.contains(search))
    
    query = query.order_by(GameResult.score.desc()).limit(100)
    
    results = []
    for result in query:
        results.append({
            'id': result.id,
            'full_name': result.user.full_name,
            'username': result.user.username,
            'score': result.score,
            'level': result.level,
            'stage': result.stage,
            'grid_size': result.grid_size,
            'duration': result.duration,
            'date': result.date.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return templates.TemplateResponse("admin/results.html", {
        "request": request,
        "user": admin_user,
        "results": results,
        "search": search
    })