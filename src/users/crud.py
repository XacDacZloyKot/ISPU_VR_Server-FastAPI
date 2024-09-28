from sqlalchemy import select, Sequence
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import User, Admission


async def get_user_for_id(user_id: int, session: AsyncSession) -> User:
    try:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user: User = result.scalars().first()
        return user
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Ошибка SQL при получении пользователя {e}")
    except Exception as e:
        raise Exception(f"Ошибка при получении пользователя {e}")


async def get_users_without_scenario(scenario_id: int, session: AsyncSession) -> Sequence[User]:
    subquery = select(Admission.user_id).where(scenario_id == Admission.scenario_id).subquery()
    result = await session.execute(select(User).where(User.id.not_in(select(subquery))))
    users_without_scenario = result.scalars().all()
    return users_without_scenario

async def get_users(session: AsyncSession) -> Sequence[User]:
    query = select(User).where(False == User.is_superuser, False == User.is_staff)
    result = await session.execute(query)
    users = result.scalars().all()
    return users