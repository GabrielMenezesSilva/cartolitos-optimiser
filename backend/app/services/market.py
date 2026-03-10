import httpx
from typing import Dict, Any, Optional

class CartolaService:
    def __init__(self):
        self.base_url = "https://api.cartola.globo.com"

    async def get_mercado_status(self) -> Dict[str, Any]:
        """Busca o status do mercado (aberto/fechado, rodada atual, times escalados)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/mercado/status")
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    async def get_atletas_mercado(self) -> Dict[str, Any]:
        """Busca todos os atletas, clubes e posições"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/atletas/mercado")
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    async def get_partidas(self, rodada: Optional[int] = None) -> Dict[str, Any]:
        """Busca as partidas de uma rodada específica ou da rodada atual se None"""
        endpoint = f"{self.base_url}/partidas/{rodada}" if rodada else f"{self.base_url}/partidas"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    async def get_historical_data(self, year: int, rodada: int) -> str:
        """Busca dados históricos brutos do repositório de referência (caRtola)"""
        url = f"https://raw.githubusercontent.com/henriquepgomide/caRtola/master/data/01_raw/{year}/rodada-{rodada}.csv"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception:
            pass
        return ""

    def calculate_mv(self, preco_atual: float, ultima_pontuacao: float) -> float:
        """Modelo de Valorização: Mínimo para Valorizar (MV)"""
        return float((preco_atual * 0.45) + (ultima_pontuacao * 0.1))

cartola_service = CartolaService()
