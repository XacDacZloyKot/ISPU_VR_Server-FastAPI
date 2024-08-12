from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import Admission, AdmissionStatus


async def update_admission_result(session: AsyncSession, admission: Admission, rating: str, status: str) -> None:
    try:
        admission.status = status
        admission.rating = rating
        session.add(admission)
        await session.commit()
    except Exception as e:
        raise Exception(f"An error occurred while update connections: {e}")