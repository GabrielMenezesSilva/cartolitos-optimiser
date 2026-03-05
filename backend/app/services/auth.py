import httpx
from typing import Dict, Any

class GloboAuthService:
    def __init__(self):
        self.auth_url = "https://login.globo.com/api/authentication"
        self.save_team_url = "https://api.cartola.globo.com/auth/time/salvar"
        
        # Headers avançados para simular um cliente real e evitar 403
        self.base_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://cartola.globo.com",
            "Referer": "https://cartola.globo.com/",
            "Connection": "keep-alive"
        }

    async def authenticate(self, email: str, password: str) -> str:
        """
        Autentica no Globo ID e retorna o X-GLB-Token (glbId).
        O Cartola usa o ServiceId 438.
        """
        payload = {
            "payload": {
                "email": email,
                "password": password,
                "serviceId": 438
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.auth_url, 
                json=payload, 
                headers=self.base_headers
            )
            response.raise_for_status()
            data = response.json()
            
            glb_id = data.get("glbId")
            if not glb_id:
                raise ValueError("glbId não encontrado na resposta de autenticação.")
            
            return glb_id

    async def save_lineup(self, glb_id: str, team_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Salva o time escalado no Cartola usando o glbId obtido.
        """
        headers = self.base_headers.copy()
        headers["X-GLB-Token"] = glb_id
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.save_team_url,
                json=team_payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

auth_service = GloboAuthService()
