from sqlalchemy.sql.expression import text
from sqlalchemy.ext.asyncio import AsyncSession


COURSES_TABLE = 'public.courses'

async def create_course(db: AsyncSession, course_name: str, course_description: str, institution_id: str):
    sql_statement = text(f"""   
        INSERT INTO {COURSES_TABLE} (course_name, course_description, institution_id)
        VALUES (:course_name, :course_description, :institution_id)
    """)

    await db.execute(sql_statement, {
        'course_name': course_name,
        'course_description': course_description,
        'institution_id': institution_id
    })


async def get_courses_by_institution(db: AsyncSession, institution_id: str):
    sql_statement = text(f"""
        SELECT course_id, course_name, course_description, institution_id
        FROM {COURSES_TABLE}
        WHERE institution_id = :institution_id
    """)

    result = await db.execute(sql_statement, {'institution_id': institution_id})

    return result.mappings().all()


async def update_course(db: AsyncSession, course_id: str, course_name: str, course_description: str):
    sql_statement = text(f"""
        UPDATE {COURSES_TABLE}
        SET course_name = :course_name,
            course_description = :course_description
        WHERE course_id = :course_id
    """)

    await db.execute(sql_statement, {
        'course_id': course_id,
        'course_name': course_name,
        'course_description': course_description
    })


async def delete_course(db: AsyncSession, course_id: str):
    sql_statement = text(f"""
        DELETE FROM {COURSES_TABLE}
        WHERE course_id = :course_id
    """)

    await db.execute(sql_statement, {'course_id': course_id}) 
    