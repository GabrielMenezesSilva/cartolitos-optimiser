from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any
from app.core.firebase import get_current_user, get_firebase_app
from firebase_admin import firestore

router = APIRouter()

class LineupSaveRequest(BaseModel):
    round_uuid: int
    expected_points_total: float
    cost: float
    teams_json: List[Dict[str, Any]]

@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_lineup(request: LineupSaveRequest, current_user: dict = Depends(get_current_user)):
    try:
        db = firestore.client()
        user_id = current_user.get("uid")
        
        # Cria ou atualiza o documento da rodada na collection lineup_history
        doc_ref = db.collection("lineup_history").document(f"{user_id}_{request.round_uuid}")
        doc_ref.set({
            "uid": user_id,
            "round_uuid": request.round_uuid,
            "expected_points_total": request.expected_points_total,
            "cost": request.cost,
            "teams_json": request.teams_json,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
        return {"status": "success", "message": "Escalação salva com sucesso para a Prova Real!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit", response_model=List[Dict[str, Any]])
async def get_audit_history(current_user: dict = Depends(get_current_user)):
    try:
        db = firestore.client()
        user_id = current_user.get("uid")
        
        # Buscar histórico de line-ups
        lineups_ref = db.collection("lineup_history").where("uid", "==", user_id).stream()
        history = []
        for doc in lineups_ref:
            history.append(doc.to_dict())
            
        # Opcional: Cruza com `round_results` se existir (poderá ser um doc mesclado depois)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
