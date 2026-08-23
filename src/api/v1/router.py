from fastapi import APIRouter
from api.v1 import auth

# The main v1 router — include all sub-routers here
api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth.router)
