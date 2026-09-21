from db.connection import get_auth_db
from services.public.admin_users import create_student_or_instructor
from schemas.auth.tokens import TokenPayload
from core import require_role
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.public.admin_users import CreateUserRequest
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/admin/users", tags=["admin-users"])

@router.post('', status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    db: AsyncSession = Depends(get_auth_db),
    current_user: TokenPayload = Depends(require_role('admin'))
):
    return await create_student_or_instructor(
        db=db,
        request=request,
        admin_user_id=current_user.sub,
        admin_institution_id=current_user.institution_id
    )