from slugify import slugify
from sqlalchemy import select, func, insert
from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from src.auth import Admission, AdmissionStatus, User, Scenario
from src.sensor import (Location,
                        LocationStatus,
                        Model,
                        Accident,
                        model_accident_association,
                        ModelValue,
                        ModelType,
                        Sensor,
                        sensor_location_association,
                        scenario_accident_association
                        )


async def get_admission_for_user_id(user_id: int, session: AsyncSession, include_completed: bool = True) -> Sequence[
    Admission]:
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
    query = select(ModelValue.model_type, func.count(ModelValue.id).label('count')).group_by(ModelValue.model_type)
    result = await session.execute(query)
    sensor_values = result.all()
    return sensor_values


async def get_sensor_value_for_name(session: AsyncSession, sensor_name: str) -> Sequence[ModelValue]:
    query = select(ModelValue).where(sensor_name == ModelValue.model_type)
    result = await session.execute(query)
    values = result.scalars().all()
    return values


async def get_sensor_values_for_id(session: AsyncSession, fields_id: list[int]) -> Sequence[ModelValue]:
    result = await session.execute(select(ModelValue).where(ModelValue.id.in_(fields_id)))
    sensor_values = result.scalars().all()
    return sensor_values


async def create_or_get_model_type(session: AsyncSession, sensor_type_name: str) -> int:
    query = select(ModelType).where(ModelType.name == sensor_type_name)
    result = await session.execute(query)
    type_model = result.scalars().first()

    if type_model:
        return type_model.id

    new_model_type = ModelType(name=sensor_type_name)
    session.add(new_model_type)
    await session.commit()

    return new_model_type.id


async def get_all_models(session: AsyncSession) -> Sequence[Model]:
    query = select(Model)
    result = await session.execute(query)
    models = result.scalars().all()
    return models


async def get_all_sensors(session: AsyncSession) -> Sequence[Sensor]:
    query = select(Sensor)
    result = await session.execute(query)
    sensors = result.scalars().all()
    return sensors


async def get_models_for_id(session: AsyncSession, models_id: list[int]) -> Sequence[Model]:
    result = await session.execute(select(Model).where(Model.id.in_(models_id)))
    models = result.scalars().all()
    return models


async def get_all_sensor_types(session: AsyncSession) -> Sequence[ModelType]:
    query = select(ModelType).order_by(ModelType.name)
    result = await session.execute(query)
    sensors_types = result.scalars().all()
    return sensors_types


async def get_all_sensor_values(session: AsyncSession) -> Sequence[ModelValue]:
    query = select(ModelValue).order_by(ModelValue.model_type)
    result = await session.execute(query)
    sensors_values = result.scalars().all()
    return sensors_values


async def get_all_sensor_values_group_type(session: AsyncSession) -> list[dict]:
    query = select(
        ModelValue.model_type,
        func.group_concat(func.concat(ModelValue.field, ': ', ModelValue.value, ' ', ModelValue.measurement)).label(
            'combined_values')
    ).group_by(ModelValue.model_type)
    result = await session.execute(query)
    result = result.all()
    result_list = []
    for model_type, combined_values in result:
        values = combined_values.split(',')
        value_dict = {}
        for value in values:
            parts = value.split(': ', 1)
            if len(parts) == 2:
                field = parts[0]
                measurement_value = parts[1].strip()
                value_dict[field] = measurement_value
        result_list.append({'name': model_type, 'value': value_dict})
    return result_list


async def delete_all_connection_location_model(session: AsyncSession, location_id: int) -> None:
    try:
        query = delete(sensor_location_association).where(sensor_location_association.c.location_id == location_id)
        await session.execute(query)
        await session.commit()
    except Exception as e:
        print(f"An error occurred while deleting connections: {e}")
        raise


async def delete_all_connection_scenario_accident(session: AsyncSession, scenario_id: int) -> None:
    try:
        query = delete(scenario_accident_association).where(scenario_accident_association.c.scenario_id == scenario_id)
        await session.execute(query)
        await session.commit()
    except Exception as e:
        print(f"An error occurred while deleting connections: {e}")
        raise


async def delete_accident_for_model(session: AsyncSession, model_id: int, accident_id: int) -> None:
    try:
        query = (
            delete(model_accident_association)
            .where(model_accident_association.c.model_id == model_id)
            .where(model_accident_association.c.accident_id == accident_id)
        )
        await session.execute(query)
        await session.commit()
    except Exception as e:
        print(f"An error occurred while deleting connections: {e}")
        raise


async def delete_accident_for_scenario(session: AsyncSession, scenario_id: int, accident_id: int) -> None:
    try:
        query = (
            delete(scenario_accident_association)
            .where(scenario_accident_association.c.scenario_id == scenario_id)
            .where(scenario_accident_association.c.accident_id == accident_id)
        )
        await session.execute(query)
        await session.commit()
    except Exception as e:
        print(f"An error occurred while deleting connections: {e}")
        raise


async def add_accidents_for_scenario(session: AsyncSession, scenario_id: int, accidents_id: list[int] | None) -> None:
    try:
        if not accidents_id:
            return None
        scenario_accidents = [
            {"scenario_id": scenario_id, "accident_id": accident_id}
            for accident_id in accidents_id
        ]
        await session.execute(insert(scenario_accident_association).values(scenario_accidents))
        await session.commit()
    except Exception as e:
        print(f"An error occurred while adding accidents: {e}")
        await session.rollback()
        raise


async def create_sensor(session: AsyncSession, KKS: str, name: str, model_id: int) -> None:
    new_sensor_type = Sensor(name=name, KKS=KKS, model_id=model_id)
    session.add(new_sensor_type)
    await session.commit()


async def create_model_value_or_none(session: AsyncSession, key: str, value: str, name: str, measurement: str,
                                     name_eng_param: str):
    name_eng_param = slugify(name_eng_param, separator='_')
    query = select(ModelValue).where(key == ModelValue.field,
                                     measurement == ModelValue.measurement, name == ModelValue.model_type)
    result = await session.execute(query)
    model_value = result.scalars().first()

    if model_value:
        model_value.value = value
        model_value.name_eng_param = name_eng_param
        session.add(model_value)
        await session.commit()
    else:
        new_model_value = ModelValue(value=value, field=key, measurement=measurement, model_type=name,
                                     name_eng_param=name_eng_param)
        type_model = ModelType(name=name)
        session.add(new_model_value)
        session.add(type_model)
        await session.commit()
        return new_model_value
