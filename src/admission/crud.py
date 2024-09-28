from sqlalchemy.exc import SQLAlchemyError

from src.auth import AdmissionStatus, Admission
from sqlalchemy import select

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession


async def get_admissions_by_user(user_id: int, session: AsyncSession,
                                    include_completed: bool = True) -> Sequence[Admission]:
    try:
        if include_completed:
            query = select(Admission).where(user_id == Admission.user_id)
        else:
            query = select(Admission).where(user_id == Admission.user_id,
                                            AdmissionStatus.COMPLETED != Admission.status)
        result = await session.execute(query)
        admission = result.scalars().all()
        return admission
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при получении задач: {e}")
        raise SQLAlchemyError("Ошибка при получении задач.")


def get_last_admission_task(list_admission_tasks: Sequence[Admission]) -> Admission | None:
    try:
        if not list_admission_tasks:
            return None
        filtered_admissions = [admission for admission in list_admission_tasks if admission.is_ready is not None]
        if not filtered_admissions:
            return None
        last_admission = max(filtered_admissions, key=lambda admission: admission.is_ready)
        return last_admission
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при получении задачи: {e}")
        raise SQLAlchemyError("Ошибка при получении задачи.")

async def get_admission_for_id(admission_id: int, session: AsyncSession) -> Admission:
    query = select(Admission).where(admission_id == Admission.id)
    result = await session.execute(query)
    admission = result.scalar_one_or_none()
    return admission


async def get_admissions(user_id: int, session: AsyncSession) -> Sequence[Admission]:
    query = select(Admission).where(user_id == Admission.user_id).order_by("status")
    result = await session.execute(query)
    admission = result.scalars().all()
    return admission