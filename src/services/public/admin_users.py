import secrets
import logging

from sqlalchemy.exc import IntegrityError
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

            examinee_id_number = None

            if request.role == 'student':
                examinee_id_number = await generate_examinee_id(db, admin_institution_id)

            await profiles.create_profile(
                db,
                user_id=user_id,
                email=request.email,
                first_name=request.first_name,
                middle_name=request.middle_name,
                last_name=request.last_name,
                role=request.role,
                institution_id=admin_institution_id,
                examinee_id_number=examinee_id_number
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
            'examinee_id_number': examinee_id_number
        }

    except IntegrityError as error:
        if 'profiles_student_examinee_id_unique' in str(error.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Examinee ID already exists within the institution'
            )

        logging.exception("Error creating user: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Unable to create user'
        ) from error


async def generate_examinee_id(db: AsyncSession, institution_id: str) -> str:
    for _ in range(20):  # Try up to 10 times to generate a unique ID
        candidate_id = str(secrets.randbelow(900000) + 100000)  # Generate a 6-digit number

        if not await profiles.examinee_id_exists(db, institution_id, candidate_id):
            return candidate_id

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail='Unable to generate a unique examinee ID after multiple attempts'
    )
        