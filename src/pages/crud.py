from sqlalchemy import select
from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import Admission, AdmissionStatus, User, Scenario
from src.sensor import Location, Model, Accident, model_accident_association


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


async def get_location_for_id(location_id: int, session: AsyncSession) -> Location:
    query = select(Location).where(location_id == Scenario.id)
    result = await session.execute(query)
    location: Location = result.scalars().first()
    return location


async def get_model_for_id(model_id: int, session: AsyncSession) -> Model:
    query = select(Model).where(model_id == Scenario.id)
    result = await session.execute(query)
    model: Model = result.scalars().first()
    return model


async def get_location_names(session: AsyncSession) -> List[dict]:
    locations_query = select(Location)
    result = await session.execute(locations_query)
    location_results = result.scalars().all()
    location_list = [{"name": str(location), "id": location.id} for location in location_results]
    return location_list


async def get_model_names(session: AsyncSession) -> List[str]:
    models_query = select(Model)
    result = await session.execute(models_query)
    model_results = result.scalars().all()
    model_list = [{"name": str(model), "id": model.id} for model in model_results]
    return model_list


async def get_accidents_for_model(session: AsyncSession, model_id: int) -> Sequence[Accident]:
    query = select(Accident).join(model_accident_association).join(Model).where(model_id == Model.id)
    result = await session.execute(query)
    accidents = result.scalars().all()
    print(accidents)
    return accidents

