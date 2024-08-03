from sqlalchemy import select, func
from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.auth import Admission, AdmissionStatus, User, Scenario
from src.sensor import (Location,
                        LocationStatus,
                        Model,
                        Accident,
                        model_accident_association,
                        SensorValue,
                        SensorType,
                        Sensor,
                        )


async def get_admission_for_user_id(user_id: int, session: AsyncSession, include_completed: bool = True) -> Sequence[Admission]:
    if include_completed:
        query = select(Admission).where(user_id == Admission.user_id)
    else:
        query = select(Admission).where(user_id == Admission.user_id,
                                        AdmissionStatus.COMPLETED != Admission.status)
    result = await session.execute(query)
    admission = result.scalars().all()
    return admission


async def get_admission_for_id(admission_id: int, session: AsyncSession) -> Admission:
    query = select(Admission).where(admission_id == Admission.id)
    result = await session.execute(query)
    admission = result.scalar_one_or_none()
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


async def get_scenarios_active_list(session: AsyncSession) -> Sequence[Scenario]:
    query = (
        select(Scenario)
        .join(Location)
        .where(LocationStatus.COMPLETED == Location.status)
    )
    result = await session.execute(query)
    scenarios = result.scalars().all()

    return scenarios


async def get_location_for_id(location_id: int, session: AsyncSession) -> Location:
    query = select(Location).where(location_id == Location.id)
    result = await session.execute(query)
    location: Location = result.scalars().first()
    return location


async def get_model_for_id(model_id: int, session: AsyncSession) -> Model:
    query = select(Model).where(model_id == Model.id)
    result = await session.execute(query)
    model: Model = result.scalars().first()
    return model


async def get_location_names(session: AsyncSession) -> List[dict]:
    locations_query = select(Location)
    result = await session.execute(locations_query)
    location_results = result.scalars().all()
    location_list = [{"name": str(location), "id": location.id} for location in location_results]
    return location_list


async def get_location_list(session: AsyncSession) -> Sequence[Location]:
    locations_query = select(Location)
    result = await session.execute(locations_query)
    location_results = result.scalars().all()
    return location_results


async def get_model_names(session: AsyncSession) -> List[dict]:
    models_query = select(Model)
    result = await session.execute(models_query)
    model_results = result.scalars().all()
    model_list = [{"name": str(model), "id": model.id} for model in model_results]
    return model_list


async def get_sensor_list(session: AsyncSession) -> Sequence[Sensor]:
    sensors_query = select(Sensor)
    result = await session.execute(sensors_query)
    sensor_results = result.scalars().all()
    return sensor_results


async def get_accidents_for_model(session: AsyncSession, model_id: int) -> Sequence[Accident]:
    query = select(Accident).join(model_accident_association).join(Model).where(model_id == Model.id)
    result = await session.execute(query)
    accidents = result.scalars().all()
    return accidents


async def get_sensor_for_id(session: AsyncSession, sensor_id: int) -> Sensor:
    query = select(Sensor).where(sensor_id == Sensor.id)
    result = await session.execute(query)
    sensor = result.scalar_one_or_none()
    return sensor


async def get_name_sensor_value(session: AsyncSession):
    query = select(SensorValue.sensor_type, func.count(SensorValue.id).label('count')).group_by(SensorValue.sensor_type)
    result = await session.execute(query)
    sensor_values = result.all()
    return sensor_values


async def get_sensor_value_for_name(session: AsyncSession, sensor_name: str) -> Sequence[SensorValue]:
    query = select(SensorValue).where(sensor_name == SensorValue.sensor_type)
    result = await session.execute(query)
    values = result.scalars().all()
    return values


async def get_sensor_values_for_id(session: AsyncSession, fields_id: list[int]) -> Sequence[SensorValue]:
    result = await session.execute(select(SensorValue).where(SensorValue.id.in_(fields_id)))
    sensor_values = result.scalars().all()
    return sensor_values


async def create_or_get_sensor_type(session: AsyncSession, sensor_type_name: str) -> int:
    query = select(SensorType).where(SensorType.name == sensor_type_name)
    result = await session.execute(query)
    sensor_type = result.scalars().first()

    if sensor_type:
        return sensor_type.id

    new_sensor_type = SensorType(name=sensor_type_name)
    session.add(new_sensor_type)
    await session.commit()

    return new_sensor_type.id


async def get_all_models(session: AsyncSession) -> Sequence[Model]:
    query = select(Model)
    result = await session.execute(query)
    models = result.scalars().all()
    return models

async def get_all_sensors(session: AsyncSession) -> Sequence[Model]:
    query = select(Sensor)
    result = await session.execute(query)
    sensors = result.scalars().all()
    return sensors


async def get_models_for_id(session: AsyncSession, models_id: list[int]) -> Sequence[Model]:
    result = await session.execute(select(Model).where(Model.id.in_(models_id)))
    models = result.scalars().all()
    return models
