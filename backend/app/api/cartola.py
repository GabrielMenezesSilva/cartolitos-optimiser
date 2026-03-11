from fastapi import APIRouter, HTTPException
from app.services.market import cartola_service
import asyncio

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


async def _ingest_historical_rounds(rodada_atual: int, num_rounds: int = 5) -> int:
    """
    Ingere múltiplas rodadas históricas para treinar os modelos de ML.
    Busca as 'num_rounds' rodadas anteriores à rodada_atual.
    Retorna o número de rodadas ingeridas com sucesso.
    """
    ingested = 0
    tasks = []

    for r in range(max(1, rodada_atual - num_rounds), rodada_atual):
        tasks.append(cartola_service.get_historical_data(2024, r))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for csv_data in results:
        if isinstance(csv_data, str) and csv_data.strip():
            data_processor.ingest_historical_csv(csv_data)
            ingested += 1

    return ingested


@router.get("/optimize-real")
async def optimize_real(
    budget: float = 140.0,
    formation: str = "4-3-3",
    ousadia: int = 5,
    modo: str = "mitagem",
    rodadas_historicas: int = 5,
):
    """
    Pipeline completo de otimização baseado na referência técnica caRtola:
    1. Busca atletas e status do mercado
    2. Ingere múltiplas rodadas históricas (Poisson real + Média Cedida + Markov + RF)
    3. Clustering Affinity Propagation por perfil técnico
    4. Treina Random Forest com features de dificuldade
    5. Resolve escalação ótima via PuLP (ILP)
    """
    try:
        # ── 1. Buscar atletas e status do mercado em paralelo ─────────
        cartola_data, status_mercado = await asyncio.gather(
            cartola_service.get_atletas_mercado(),
            cartola_service.get_mercado_status(),
            return_exceptions=False,
        )

        rodada_atual = int(status_mercado.get('rodada_atual', 2)) if isinstance(status_mercado, dict) else 2

        # ── 2. Ingerir múltiplas rodadas históricas em paralelo ───────
        ingested_count = 0
        try:
            ingested_count = await _ingest_historical_rounds(rodada_atual, num_rounds=rodadas_historicas)
        except Exception:
            pass  # Continua sem histórico; modelos usarão fallbacks

        # ── 3. Buscar partidas da rodada atual para contexto ──────────
        cartola_partidas = None
        try:
            cartola_partidas = await cartola_service.get_partidas()
        except Exception:
            pass

        # ── 4. Normalizar jogadores (roda o pipeline ML completo) ─────
        players_normalized = data_processor.normalize_players(
            cartola_data,
            objective=modo,
            cartola_partidas=cartola_partidas,
            ousadia=ousadia,
        )

        # ── 5. Resolver escalação com Motor Matemático (PuLP ILP) ─────
        engine = MathEngine(budget=budget, formation=formation, objective=modo)
        result = engine.optimize_team(players_normalized)

        # ── 6. Enriquecer metadados do resultado ──────────────────────
        titulares = [p for p in result["results"]["lineup"] if p["is_titular"]]
        reservas = [p for p in result["results"]["lineup"] if not p["is_titular"]]
        
        # Calcular valorização esperada baseada na fórmula interna (pts_valorizacao * fator_c)
        pts_val = sum(p.get("pontos_valorizacao", 0.0) for p in titulares)
        expected_val_cs = pts_val * 0.45
        
        result["meta"]["roi_cartoletas"] = (
            expected_val_cs if modo == "valorizacao" else (expected_val_cs * 0.5) 
            # O modo mitagem ainda ganha algumas cartoletas, mas menos.
        )
        result["meta"]["expected_valorization"] = expected_val_cs
        
        # Inserir previsão de Melhores SGs da rodada
        result["meta"]["top_sgs"] = data_processor.get_top_sgs(cartola_partidas, cartola_data)
        
        result["meta"]["score_protecao"] = (
            sum(p["pontos_esperados"] for p in reservas) / max(1, len(reservas))
        )
        result["meta"]["rodadas_historicas_ingeridas"] = ingested_count
        result["meta"]["ml_pipeline_fitted"] = data_processor._pipeline_fitted
        result["meta"]["rf_trained"] = data_processor.rf_predictor._is_fitted
        result["meta"]["clustering_fitted"] = data_processor.clusterer._is_fitted

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no pipeline full: {str(e)}")


@router.get("/optimize-real/multiple")
async def optimize_real_multiple(
    budget: float = 140.0,
    formation: str = "4-3-3",
    ousadia: int = 5,
    modo: str = "mitagem",
    rodadas_historicas: int = 5,
    num_lineups: int = 3,
):
    """
    Gera até `num_lineups` escalações distintas usando no-good cuts no solver ILP.
    Cada escalação tem pelo menos 1 jogador diferente da anterior.
    """
    try:
        cartola_data, status_mercado = await asyncio.gather(
            cartola_service.get_atletas_mercado(),
            cartola_service.get_mercado_status(),
            return_exceptions=False,
        )

        rodada_atual = int(status_mercado.get('rodada_atual', 2)) if isinstance(status_mercado, dict) else 2

        ingested_count = 0
        try:
            ingested_count = await _ingest_historical_rounds(rodada_atual, num_rounds=rodadas_historicas)
        except Exception:
            pass

        cartola_partidas = None
        try:
            cartola_partidas = await cartola_service.get_partidas()
        except Exception:
            pass

        players_normalized = data_processor.normalize_players(
            cartola_data,
            objective=modo,
            cartola_partidas=cartola_partidas,
            ousadia=ousadia,
        )

        engine = MathEngine(budget=budget, formation=formation, objective=modo)
        lineups = engine.optimize_multiple(players_normalized, num_lineups=min(num_lineups, 5))

        # Enrich each lineup metadata
        for result in lineups:
            titulares = [p for p in result["results"]["lineup"] if p["is_titular"]]
            reservas = [p for p in result["results"]["lineup"] if not p["is_titular"]]
            pts_val = sum(p.get("pontos_valorizacao", 0.0) for p in titulares)
            expected_val_cs = pts_val * 0.45
            result["meta"]["roi_cartoletas"] = expected_val_cs if modo == "valorizacao" else expected_val_cs * 0.5
            result["meta"]["expected_valorization"] = expected_val_cs
            result["meta"]["top_sgs"] = data_processor.get_top_sgs(cartola_partidas, cartola_data)
            result["meta"]["score_protecao"] = sum(p["pontos_esperados"] for p in reservas) / max(1, len(reservas))
            result["meta"]["rodadas_historicas_ingeridas"] = ingested_count

        return {"lineups": lineups, "total": len(lineups)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no pipeline múltiplas escalações: {str(e)}")
