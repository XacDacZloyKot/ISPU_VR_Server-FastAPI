from typing import Sequence

from slugify import slugify
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.sensor import (Model, ModelValue, ModelType, model_accident_association
                        )

async def get_model_for_id(model_id: int, session: AsyncSession) -> Model:
    query = select(Model).where(model_id == Model.id)
    result = await session.execute(query)
    model: Model = result.scalars().first()
    return model


async def get_model_values_group_by_type(session: AsyncSession) -> list[dict]:
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


async def get_model_value_for_name(session: AsyncSession, sensor_name: str) -> Sequence[ModelValue]:
    query = select(ModelValue).where(sensor_name == ModelValue.model_type)
    result = await session.execute(query)
    values = result.scalars().all()
    return values

async def create_or_get_model_type(session: AsyncSession, model_type_name: str) -> int:
    query = select(ModelType).where(model_type_name == ModelType.name)
    result = await session.execute(query)
    type_model = result.scalars().first()
    if type_model:
        return type_model.id
    new_model_type = ModelType(name=model_type_name)
    session.add(new_model_type)
    await session.commit()

    return new_model_type.id


async def get_model_values_for_id(session: AsyncSession, fields_id: list[int]) -> Sequence[ModelValue]:
    result = await session.execute(select(ModelValue).where(ModelValue.id.in_(fields_id)))
    sensor_values = result.scalars().all()
    return sensor_values



async def create_model(session: AsyncSession, fields_id: list[int], model_name: str) -> Model:
    fields = await get_model_values_for_id(session=session, fields_id=fields_id)
    fields_dict = dict()
    name_eng_params = dict()
    for field in fields:
        fields_dict[field.field] = f"{field.value} {field.measurement}"
        name_eng_params[field.field] = field.name_eng_param
    id: int = await create_or_get_model_type(session=session, model_type_name=model_name)
    new_model = Model(specification=fields_dict, param_mapping_names=name_eng_params, model_type_id=id)
    session.add(new_model)
    await session.commit()
    return new_model


async def get_models(session: AsyncSession) -> Sequence[Model]:
    query = select(Model)
    result = await session.execute(query)
    models = result.scalars().all()
    return models

async def update_model(model: Model, specification: dict, model_type_id: int, session: AsyncSession):
    model.specification = specification
    model.model_type_id = model_type_id
    session.add(model)
    await session.commit()


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


async def create_model_values_or_update(session: AsyncSession, keys: list[str], values: list[str],
                                        measurements: list[str], name_eng_params: list[str], name: str):
    for i in range(len(keys)):
        name_eng_param = slugify(name_eng_params[i], separator='_')

        query = select(ModelValue).where(
            keys[i] == ModelValue.field, name == ModelValue.model_type
        )
        result = await session.execute(query)
        model_value = result.scalars().first()

        if model_value:
            model_value.value = values[i]
            model_value.measurement = measurements[i]
            model_value.name_eng_param = name_eng_param
            session.add(model_value)
            await session.commit()

        else:
            new_model_value = ModelValue(value=values[i], field=keys[i], measurement=measurements[i],
                                         model_type=name, name_eng_param=name_eng_param)
            session.add(new_model_value)

    query = select(ModelType).where(name == ModelType.name)
    result = await session.execute(query)
    model_type = result.scalar_one_or_none()
    if not model_type:
        type_model = ModelType(name=name)
        session.add(type_model)
    await session.commit()