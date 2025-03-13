# app/routes/game_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Form
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user
from app.models import User, GameResult, GameProgress
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from peewee import fn
from datetime import datetime
import json

router = APIRouter(tags=["Game"])
templates = Jinja2Templates(directory="app/templates")

class GameResultRequest(BaseModel):
    score: int
    level: int
    stage: int
    grid_size: int
    duration: int
    completed: bool

class GameProgressRequest(BaseModel):
    level: int
    stage: int
    grid_size: int
    score: int
    sequence: List[int]

@router.get("/game")
async def game_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("game.html", {
        "request": request,
        "user": current_user
    })

@router.get("/leaderboard")
async def leaderboard_page(
    request: Request, 
    region: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None),
    max_age: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    # En yuqori ballga ega foydalanuvchilar 
    query = (GameResult
             .select(GameResult, User)
             .join(User)
             .group_by(GameResult.user)  # Har bir foydalanuvchi uchun bitta natija
             .having(GameResult.score == fn.MAX(GameResult.score)))  # Har bir foydalanuvchi uchun eng yuqori balli
    
    if region and region.strip():
        query = query.where(User.region == region)
    
    current_year = datetime.now().year
    
    if min_age is not None:
        query = query.where(current_year - fn.strftime('%Y', User.birthdate).cast('integer') >= min_age)
    
    if max_age is not None:
        query = query.where(current_year - fn.strftime('%Y', User.birthdate).cast('integer') <= max_age)
    
    if search and search.strip():
        query = query.where(User.full_name.contains(search))
    
    query = query.order_by(GameResult.score.desc()).limit(100)
    
    results = []
    for result in query:
        results.append({
            'id': result.id,
            'full_name': result.user.full_name,
            'birthdate': result.user.birthdate,
            'region': result.user.region,
            'district': result.user.district,
            'score': result.score,
            'level': result.level,
            'stage': result.stage,
            'grid_size': result.grid_size,
            'duration': result.duration,
            'date': result.date.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # Get all regions for filter
    regions = []
    for user in User.select(User.region).distinct():
        if user.region not in regions:
            regions.append(user.region)
    
    return templates.TemplateResponse("leaderboard.html", {
        "request": request,
        "user": current_user,
        "results": results,
        "regions": regions,
        "filters": {
            "region": region,
            "min_age": min_age,
            "max_age": max_age,
            "search": search
        }
    })

@router.post("/api/save-result")
async def save_game_result(
    result: GameResultRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # Add coins for completing a stage
        coins_to_add = 1  # 1 coin per stage
        current_user.coins += coins_to_add
        current_user.save()
        
        # Foydalanuvchining mavjud eng yuqori balini tekshirish
        best_result = GameResult.select().where(
            GameResult.user == current_user
        ).order_by(GameResult.score.desc()).first()
        
        # Agar yangi natija oldingi yuqori natijadan yaxshiroq bo'lsa, yangilash
        if best_result:
            if result.score > best_result.score:
                # Eski natijani yangilash
                best_result.score = result.score
                best_result.level = result.level
                best_result.stage = result.stage
                best_result.grid_size = result.grid_size
                best_result.duration = result.duration
                best_result.completed = result.completed
                best_result.date = datetime.now()
                best_result.save()
                return {"status": "success", "message": "Natija yangilandi", "coins_added": coins_to_add, "total_coins": current_user.coins}
            else:
                # Agar yangi natija yaxshiroq bo'lmasa, hech narsa qilmaymiz
                return {"status": "info", "message": "Oldingi natijangiz yuqoriroq", "coins_added": coins_to_add, "total_coins": current_user.coins}
        else:
            # Foydalanuvchi uchun yangi natija yaratish
            game_result = GameResult.create(
                user=current_user,
                score=result.score,
                level=result.level,
                stage=result.stage,
                grid_size=result.grid_size,
                duration=result.duration,
                completed=result.completed
            )
            return {"status": "success", "message": "Natija muvaffaqiyatli saqlandi", "coins_added": coins_to_add, "total_coins": current_user.coins}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Natijani saqlashda xatolik: {str(e)}")

@router.post("/api/save-progress")
async def save_game_progress(
    progress: GameProgressRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # Delete previous progress
        GameProgress.delete().where(GameProgress.user == current_user).execute()
        
        # Create new progress
        game_progress = GameProgress.create(
            user=current_user,
            level=progress.level,
            stage=progress.stage,
            grid_size=progress.grid_size,
            score=progress.score,
            sequence=json.dumps(progress.sequence)
        )
        
        return {"status": "success", "message": "O'yin holati saqlandi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"O'yin holatini saqlashda xatolik: {str(e)}")

@router.get("/api/get-progress")
async def get_game_progress(current_user: User = Depends(get_current_user)):
    try:
        progress = GameProgress.get_or_none(GameProgress.user == current_user)
        
        if progress:
            return {
                "status": "success",
                "has_progress": True,
                "progress": {
                    "level": progress.level,
                    "stage": progress.stage,
                    "grid_size": progress.grid_size,
                    "score": progress.score,
                    "sequence": json.loads(progress.sequence)
                }
            }
        else:
            return {
                "status": "success",
                "has_progress": False
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"O'yin holatini olishda xatolik: {str(e)}")

@router.post("/api/use-coins")
async def use_coins_to_continue(current_user: User = Depends(get_current_user)):
    COINS_REQUIRED = 20
    
    if current_user.coins < COINS_REQUIRED:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": f"O'yinni davom ettirish uchun {COINS_REQUIRED} coin kerak. Sizda {current_user.coins} coin bor."}
        )
    
    # Deduct coins
    current_user.coins -= COINS_REQUIRED
    current_user.save()
    
    return {
        "status": "success", 
        "message": f"{COINS_REQUIRED} coin sarflandi. O'yin davom ettirilmoqda.", 
        "remaining_coins": current_user.coins
    }

@router.get("/api/user-stats")
async def get_user_stats(current_user: User = Depends(get_current_user)):
    # Get best score
    best_score_query = GameResult.select(fn.MAX(GameResult.score)).where(GameResult.user == current_user)
    best_score = best_score_query.scalar() or 0
    
    # Get highest level reached
    max_level_query = GameResult.select(fn.MAX(GameResult.level)).where(GameResult.user == current_user)
    max_level = max_level_query.scalar() or 0
    
    # Get max grid size
    max_grid_size_query = GameResult.select(fn.MAX(GameResult.grid_size)).where(GameResult.user == current_user)
    max_grid_size = max_grid_size_query.scalar() or 0
    
    # Get total games played
    games_played_query = GameResult.select(fn.COUNT(GameResult.id)).where(GameResult.user == current_user)
    games_played = games_played_query.scalar() or 0
    
    return {
        "best_score": best_score,
        "max_level": max_level,
        "max_grid_size": max_grid_size,
        "games_played": games_played,
        "coins": current_user.coins
    }