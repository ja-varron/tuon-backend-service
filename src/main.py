# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request 
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware 
# pyrefly: ignore [missing-import]
from slowapi import Limiter, _rate_limit_exceeded_handler 
# pyrefly: ignore [missing-import]
from slowapi.errors import RateLimitExceeded 
# pyrefly: ignore [missing-import]
from slowapi.util import get_remote_address 
from src.auth.router import router as auth_router 

limiter = Limiter(key_func=get_remote_address) 
app = FastAPI() 
app.state.limiter = limiter 
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) 

# pyrefly: ignore [untyped-call-args]
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:8000/"], allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"]) 
app.include_router(auth_router)