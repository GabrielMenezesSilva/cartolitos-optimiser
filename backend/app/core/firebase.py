import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_firebase_app():
    if not firebase_admin._apps:
        # Quando rodamos em cloud (Firebase Functions/Cloud Run) ele pega o default credential se não passar nada.
        # Localmente podemos usar as credenciais default do ADC ou o firebase simulator.
        # Aqui, vamos iniciar sem param que irá usar Application Default Credentials.
        cred = credentials.ApplicationDefault()
        try:
            firebase_admin.initialize_app(cred)
        except ValueError:
            # Se já inicializado ignora
            pass
    return firebase_admin.get_app()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # Verifica e decodifica o token JWT enviado pelo frontend (Firebase Auth)
        get_firebase_app()
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token de autenticação inválido ou expirado: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
