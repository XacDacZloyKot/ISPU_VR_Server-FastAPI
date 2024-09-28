from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.sensor import (Sensor)


async def get_sensor_for_id(session: AsyncSession, sensor_id: int) -> Sensor:
    query = select(Sensor).where(sensor_id == Sensor.id)
    result = await session.execute(query)
    sensor: Sensor = result.scalar_one_or_none()
    return sensor


async def create_sensor(session: AsyncSession, KKS: str, name: str, model_id: int) -> None:
    new_sensor_type = Sensor(name=name, KKS=KKS, model_id=model_id)
    session.add(new_sensor_type)
    await session.commit()


async def get_sensors(session: AsyncSession) -> Sequence[Sensor]:
    query = select(Sensor)
    result = await session.execute(query)
    sensors = result.scalars().all()
    return sensors

async def update_sensor(sensor: Sensor, model_id: int, name: str, KKS: str, session: AsyncSession) -> Sensor:
    sensor.KKS = KKS
    sensor.name = name
    sensor.model_id = model_id
    session.add(sensor)
    await session.commit()
    return sensor