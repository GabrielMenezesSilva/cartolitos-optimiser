import os
from supabase import create_client, Client
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_supabase_client() -> Client:
    supabase_url = os.environ.get("SUPABASE_URL", "https://vnufdzfedzncdiyxujgp.supabase.co")
    # For backend operations, it's better to use Service Role key, but we will use the anon key if not provided
    supabase_key = os.environ.get("SUPABASE_KEY", "sb_publishable_qL4gq2cbnLCAZuWjvyVFKw__BsLsXcd")
    
    if not supabase_key:
        raise ValueError("SUPABASE_KEY não configurada no ambiente")
    return create_client(supabase_url, supabase_key)

async def get_current_user():
    # Authentication temporarily disabled as requested
    return {"id": "dummy_user_auth_disabled", "email": "dummy@cartolitos.local"}
