from fastapi import APIRouter
from app.api.cartola import router as cartola_router
from app.api.solver import router as solver_router
from app.api.history import router as history_router

api_router = APIRouter()
api_router.include_router(cartola_router, prefix="/cartola", tags=["cartola"])
api_router.include_router(solver_router, prefix="/solver", tags=["solver"])
api_router.include_router(history_router, prefix="/history", tags=["history"])
