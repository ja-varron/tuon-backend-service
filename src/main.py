from fastapi import FastAPI, Request 
from fastapi.middleware.cors import CORSMiddleware 
from slowapi import Limiter, _rate_limit_exceeded_handler 
from slowapi.errors import RateLimitExceeded 
from slowapi.util import get_remote_address 
from .auth.router import router as auth_router 

limiter = Limiter(key_func=get_remote_address) 
app = FastAPI() 
app.state.limiter = limiter 
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) 

app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:8000/"], allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"]) 
app.include_router(auth_router)