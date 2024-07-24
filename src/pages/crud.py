from sqlalchemy import select, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import Admission, AdmissionStatus, User, Scenario


async def get_admission_for_id(user_id: int, session: AsyncSession, include_completed: bool = True) -> Sequence[Admission]:
    if include_completed:
        query = select(Admission).where(user_id == Admission.user_id)
    else:
        query = select(Admission).where(user_id == Admission.user_id,
                                        AdmissionStatus.COMPLETED != Admission.status)
    result = await session.execute(query)
    admission = result.scalars().all()
    return admission


async def get_user_for_id(user_id: int, session: AsyncSession) -> User:
    query = select(User).where(user_id == User.id)
    result = await session.execute(query)
    user: User = result.scalars().first()
    return user


async def get_users_without_scenario(scenario_id: int, session: AsyncSession) -> Sequence[User]:
    subquery = select(Admission.user_id).where(scenario_id == Admission.scenario_id).subquery()
    result = await session.execute(select(User).where(User.id.not_in(select(subquery))))
    users_without_scenario = result.scalars().all()
    return users_without_scenario


async def get_scenario_for_id(scenario_id: int, session: AsyncSession) -> Scenario:
    query = select(Scenario).where(scenario_id == Scenario.id)
    result = await session.execute(query)
    scenario: Scenario = result.scalars().first()
    return scenario

