from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any
from app.core.supabase import get_current_user, get_supabase_client

router = APIRouter()

class LineupSaveRequest(BaseModel):
    round_uuid: int
    expected_points_total: float
    cost: float
    teams_json: List[Dict[str, Any]]

@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_lineup(request: LineupSaveRequest, current_user = Depends(get_current_user)):
    try:
        supabase = get_supabase_client()
        user_id = current_user.id
        
        data = {
            "uid": user_id,
            "round_uuid": request.round_uuid,
            "expected_points_total": request.expected_points_total,
            "cost": request.cost,
            "teams_json": request.teams_json
        }
        
        # Upsert into lineup_history tables
        # requires table to be configured in Supabase with these columns
        response = supabase.table("lineup_history").upsert(data).execute()
        
        return {"status": "success", "message": "Escalação salva com sucesso para a Prova Real!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit", response_model=List[Dict[str, Any]])
async def get_audit_history(current_user = Depends(get_current_user)):
    try:
        supabase = get_supabase_client()
        user_id = current_user.id
        
        # Buscar histórico de line-ups
        response = supabase.table("lineup_history").select("*").eq("uid", user_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
