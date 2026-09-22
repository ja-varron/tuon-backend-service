from repositories.public.courses import delete_course
from repositories.public.courses import update_course
from repositories.public.courses import get_courses_by_institution
from fastapi import status
from fastapi import HTTPException
from repositories.public.courses import create_course
from schemas.public.courses import CreateCourseRequest
from db.rls import set_rls_user
import logging

from sqlalchemy.ext.asyncio import AsyncSession

async def create_admin_course(
    db: AsyncSession, 
    request: CreateCourseRequest, 
    admin_user_id: str, 
    admin_institution_id: str
):
    try:
        async with db.begin():
            await set_rls_user(db, admin_user_id)

            await create_course(
                db,
                course_name=request.name,
                course_description=request.description,
                institution_id=admin_institution_id
            )
        
        
    except Exception as error:
        logging.exception("Error creating course: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Unable to create course'
        ) from error


async def get_admin_courses(db: AsyncSession, institution_id: str, user_id: str):
    try:
        async with db.begin():
            await set_rls_user(db, user_id)
            return await get_courses_by_institution(db, institution_id)
    except Exception as error:
        logging.exception("Error fetching courses: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Unable to fetch courses'
        ) from error


async def update_admin_course(db: AsyncSession, course_id: str, course_name: str, course_description: str, user_id: str):
    try:
        async with db.begin():
            await set_rls_user(db, user_id)
            await update_course(db, course_id, course_name, course_description)
    except Exception as error:
        logging.exception("Error updating course: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Unable to update course'
        ) from error



async def delete_admin_course(db: AsyncSession, course_id: str, user_id: str):
    try:
        async with db.begin():
            await set_rls_user(db, user_id)
            await delete_course(db, course_id)
    except Exception as error:
        logging.exception("Error deleting course: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Unable to delete course'
        ) from error