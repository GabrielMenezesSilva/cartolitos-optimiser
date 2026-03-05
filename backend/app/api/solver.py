from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.solver import MathEngine

router = APIRouter()

class PlayerIn(BaseModel):
    id: int
    nome: str
    pos: int = Field(..., description="1:GOL, 2:LAT, 3:ZAG, 4:MEI, 5:ATA, 6:TEC")
    preco: float
    pontos_esperados: float
    clube_id: int

class OptimizeRequest(BaseModel):
    budget: float = Field(100.0, description="Orçamento disponível em cartoletas")
    formation: str = Field("4-3-3", description="Formação tática, ex: 4-4-2, 3-5-2")
    players: List[PlayerIn]

@router.post("/optimize")
def optimize_lineup(request: OptimizeRequest):
    """
    Recebe uma lista de jogadores com pontos esperados e preços,
    e retorna a escalação ideal maximizando os pontos dentro do orçamento.
    """
    try:
        engine = MathEngine(budget=request.budget, formation=request.formation)
        
        # Converter para lista de dicionários para o solver
        players_dict = [p.model_dump() for p in request.players]
        
        result = engine.optimize_team(players_dict)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no solver: {str(e)}")
