from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Motor Matemático de Otimização e Ingestão de Dados do Cartola FC"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Cartolitos Optimiser API. Engine is ready."}

# Incluir rotas
from app.api import api_router
from app.core.config import settings

app.include_router(api_router, prefix=settings.API_V1_STR)
