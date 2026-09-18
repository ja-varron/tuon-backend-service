import logging

from fastapi import HTTPException, status
from core import generate_password_hash
from db.rls import set_rls_user
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.public.admin_users import CreateUserRequest
from repositories import users, profiles
from services import message


async def create_student_or_instructor(
    db: AsyncSession,
    request: CreateUserRequest,
    admin_user_id: str,
    admin_institution_id: str
):
    try:
        async with db.begin():
            await set_rls_user(db, admin_user_id)

            hashed_password = generate_password_hash(request.password)

            user_id = await users.create_user_from_admin(
                db,
                email=request.email,
                hashed_password=hashed_password,
            )

            await profiles.create_profile(
                db,
                user_id=user_id,
                email=request.email,
                first_name=request.first_name,
                middle_name=request.middle_name,
                last_name=request.last_name,
                role=request.role,
                institution_id=admin_institution_id
            )

            await message.send_account_creation_email(
                email=request.email,
                password=request.password,
                role=request.role.capitalize(),
            )

        return {
            'user_id': str(user_id),
            'email': request.email,
            'role': request.role,
        }

    except Exception as error:
        logging.exception("Error creating user: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Unable to create user'
        ) from error