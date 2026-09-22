
from services.public.courses import delete_admin_course
from services.public.courses import update_admin_course
from fastapi import HTTPException
from uuid import UUID
from services.public.courses import get_admin_courses
from services.public.courses import create_admin_course
from core import require_role
from schemas.auth.tokens import TokenPayload
from db.connection import get_public_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.public.courses import CreateCourseRequest
from fastapi import status
from fastapi import APIRouter

router = APIRouter(prefix="/courses", tags=["courses"])

@router.post('', status_code=status.HTTP_201_CREATED)
async def create_course_router(
    request: CreateCourseRequest,
    db: AsyncSession = Depends(get_public_db),
    current_user: TokenPayload = Depends(require_role('admin'))
):
    await create_admin_course(
        db=db,
        request=request,
        admin_user_id=current_user.sub,
        admin_institution_id=current_user.institution_id
    )

    return {
        'name': request.name,
        'description': request.description,
        'institution_id': current_user.institution_id
    }



@router.get('/{institution_id}', status_code=status.HTTP_200_OK)
async def get_courses_router(
    institution_id: UUID,
    db: AsyncSession = Depends(get_public_db),
    current_user: TokenPayload = Depends(require_role('admin'))
):
    if str(institution_id) != current_user.institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You do not have permission to access courses for this institution'
        )

    return await get_admin_courses(
        db=db,
        institution_id=str(institution_id),
        user_id=current_user.sub
    )   


@router.put('/{course_id}', status_code=status.HTTP_200_OK)
async def update_course_router(
    course_id: UUID,
    request: CreateCourseRequest,
    db: AsyncSession = Depends(get_public_db),
    current_user: TokenPayload = Depends(require_role('admin'))
):
    await update_admin_course(
        db=db,
        course_id=str(course_id),
        course_name=request.name,
        course_description=request.description,
        user_id=current_user.sub
    )

    return {
        'course_id': str(course_id),
        'name': request.name,
        'description': request.description
    }


@router.delete('/{course_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_course_router(
    course_id: UUID,
    db: AsyncSession = Depends(get_public_db),
    current_user: TokenPayload = Depends(require_role('admin'))
):
    await delete_admin_course(
        db=db,
        course_id=str(course_id),
        user_id=current_user.sub
    )