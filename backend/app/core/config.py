from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cartolitos Optimiser"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    REDIS_URL: str = "redis://localhost:6379"
    
    # Cartola URLs
    CARTOLA_API_BASE_URL: str = "https://api.cartola.globo.com"
    GLOBO_LOGIN_URL: str = "https://login.globo.com/api/authentication"

    class Config:
        env_file = ".env"

settings = Settings()
