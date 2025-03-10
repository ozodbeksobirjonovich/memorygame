from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user
from app.database import get_db
from app.models import GameResult
import aiosqlite
from typing import List, Optional

router = APIRouter(tags=["Game"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/game")
async def game_page(request: Request, current_user = Depends(get_current_user)):
    return templates.TemplateResponse("game.html", {
        "request": request,
        "user": current_user
    })

@router.get("/leaderboard")
async def leaderboard_page(
    request: Request, 
    region: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    search: Optional[str] = None,
    db = Depends(get_db)
):
    query = """
    SELECT 
        r.id, 
        u.full_name, 
        u.birthdate, 
        u.region, 
        u.district, 
        r.score, 
        r.level, 
        r.stage, 
        r.grid_size, 
        r.date,
        r.duration
    FROM game_results r
    JOIN users u ON r.user_id = u.id
    WHERE 1=1
    """
    params = []
    
    if region:
        query += " AND u.region = ?"
        params.append(region)
    
    if min_age:
        query += " AND (strftime('%Y', 'now') - strftime('%Y', u.birthdate)) >= ?"
        params.append(min_age)
    
    if max_age:
        query += " AND (strftime('%Y', 'now') - strftime('%Y', u.birthdate)) <= ?"
        params.append(max_age)
    
    if search:
        query += " AND u.full_name LIKE ?"
        params.append(f"%{search}%")
    
    query += " ORDER BY r.score DESC LIMIT 100"
    
    async with db.execute(query, params) as cursor:
        results = [dict(row) for row in await cursor.fetchall()]
    
    # Get all regions for filter
    async with db.execute("SELECT DISTINCT region FROM users") as cursor:
        regions = [dict(row)["region"] for row in await cursor.fetchall()]
    
    return templates.TemplateResponse("leaderboard.html", {
        "request": request,
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
    result: GameResult,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    # Verify the user_id in the result matches the current user
    if result.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        await db.execute("""
        INSERT INTO game_results 
        (user_id, score, level, stage, grid_size, duration, completed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            result.user_id,
            result.score,
            result.level,
            result.stage,
            result.grid_size,
            result.duration,
            result.completed
        ))
        await db.commit()
        
        return {"status": "success", "message": "Result saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save result: {str(e)}")

@router.get("/api/user-stats")
async def get_user_stats(current_user = Depends(get_current_user), db = Depends(get_db)):
    user_id = current_user["id"]
    
    # Get best score
    async with db.execute(
        "SELECT MAX(score) as best_score FROM game_results WHERE user_id = ?", 
        (user_id,)
    ) as cursor:
        best_score_row = await cursor.fetchone()
        best_score = best_score_row["best_score"] if best_score_row and best_score_row["best_score"] else 0
    
    # Get highest level reached
    async with db.execute(
        "SELECT MAX(level) as max_level, MAX(grid_size) as max_grid_size FROM game_results WHERE user_id = ?", 
        (user_id,)
    ) as cursor:
        level_row = await cursor.fetchone()
        max_level = level_row["max_level"] if level_row and level_row["max_level"] else 0
        max_grid_size = level_row["max_grid_size"] if level_row and level_row["max_grid_size"] else 0
    
    # Get total games played
    async with db.execute(
        "SELECT COUNT(*) as games_played FROM game_results WHERE user_id = ?", 
        (user_id,)
    ) as cursor:
        games_row = await cursor.fetchone()
        games_played = games_row["games_played"] if games_row else 0
    
    return {
        "best_score": best_score,
        "max_level": max_level,
        "max_grid_size": max_grid_size,
        "games_played": games_played
    }