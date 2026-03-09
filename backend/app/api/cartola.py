from fastapi import APIRouter, HTTPException
from app.services.market import cartola_service

router = APIRouter()

@router.get("/status")
async def get_status():
    """Retorna o status atual do mercado do Cartola."""
    try:
        return await cartola_service.get_mercado_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/atletas")
async def get_atletas():
    """Retorna todos os atletas disponíveis no mercado."""
    try:
        return await cartola_service.get_atletas_mercado()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from typing import Optional

@router.get("/partidas")
async def get_partidas(rodada: Optional[int] = None):
    """Retorna as partidas, opcionalmente de uma rodada específica."""
    try:
        return await cartola_service.get_partidas(rodada)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.services.analytics import data_processor
from app.services.solver import MathEngine

@router.get("/optimize-real")
async def optimize_real(budget: float = 140.0, formation: str = "4-3-3", ousadia: int = 5, modo: str = "mitagem"):
    """
    Busca os atletas reais no Cartola API, normaliza com o peso de Ousadia, 
    e resolve a escalação ótima.
    """
    try:
        # 1. Obter Atletas da API
        cartola_data = await cartola_service.get_atletas_mercado()
        
        # 1.5 Obter Partidas da API para Multiplicador de Contexto (FDR)
        try:
            cartola_partidas = await cartola_service.get_partidas()
        except Exception:
            # Caso a API de partidas falhe ou esteja fora do ar, ignora o bônus
            cartola_partidas = None
        
        # 2. Processar e Normalizar
        players_normalized = data_processor.normalize_players(
            cartola_data, 
            ousadia=ousadia, 
            objective=modo, 
            cartola_partidas=cartola_partidas
        )
        
        # 3. Resolver com Motor Matemático
        engine = MathEngine(budget=budget, formation=formation, objective=modo)
        result = engine.optimize_team(players_normalized)
        
        # 4. RF02 : Simulador de Impacto / ROI Extras
        reservas = [p for p in result["results"]["lineup"] if not p["is_titular"]]
        result["meta"]["roi_cartoletas"] = result["meta"]["total_expected_points"] * 0.45 if modo == "valorizacao" else 0.0
        result["meta"]["score_protecao"] = sum(p['pontos_esperados'] for p in reservas) / max(1, len(reservas))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no pipeline full: {str(e)}")
