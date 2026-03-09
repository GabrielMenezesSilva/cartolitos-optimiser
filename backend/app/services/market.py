import httpx
from typing import Dict, Any

class CartolaService:
    def __init__(self):
        self.base_url = "https://api.cartola.globo.com"

    async def get_mercado_status(self) -> Dict[str, Any]:
        """Busca o status do mercado (aberto/fechado, rodada atual, times escalados)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/mercado/status")
            response.raise_for_status()
            return response.json()

    async def get_atletas_mercado(self) -> Dict[str, Any]:
        """Busca todos os atletas, clubes e posições"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/atletas/mercado")
            response.raise_for_status()
            return response.json()

    async def get_partidas(self, rodada: int = None) -> Dict[str, Any]:
        """Busca as partidas de uma rodada específica ou da rodada atual se None"""
        endpoint = f"{self.base_url}/partidas/{rodada}" if rodada else f"{self.base_url}/partidas"
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            return response.json()

cartola_service = CartolaService()
