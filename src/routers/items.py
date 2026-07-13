from src.auth.router import router
# pyrefly: ignore [missing-import]
from fastapi import Depends
from src.dependencies import get_current_user, require_role

@router.get("/items")
async def list_items(user=Depends(get_current_user)):
  return { 
    "user_id": user["id"],
    "items": [...]
  }

@router.delete("/items/{id}") 
async def delete_item(id: str, user=Depends(require_role("admin"))): 
  return {"deleted": id} # app/main.py — protect an entire router prefix from app.dependencies import get_current_user app.include_router( items_router, prefix="/api/v1", dependencies=[Depends(get_current_user)] # applies to all routes )