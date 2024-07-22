from sqlalchemy import select, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import Admission, AdmissionStatus, User


async def admission_for_id(user_id: int, session: AsyncSession, include_completed: bool = True) -> Sequence[Admission]:
    if include_completed:
        query = select(Admission).where(user_id == Admission.user_id)
    else:
        query = select(Admission).where(user_id == Admission.user_id,
                                        AdmissionStatus.COMPLETED != Admission.status)
    result = await session.execute(query)
    admission = result.scalars().all()
    return admission


async def user_for_id(user_id: int, session: AsyncSession) -> User:
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user: User = result.scalars().first()
    return user
