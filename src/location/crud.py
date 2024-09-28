from typing import Sequence

from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.sensor import (Location, LocationStatus, sensor_location_association
                        )


async def get_locations(session: AsyncSession) -> Sequence[Location]:
    query = select(Location)
    result = await session.execute(query)
    results = result.scalars().all()
    return results


async def get_location_for_id(location_id: int, session: AsyncSession) -> Location:
    query = select(Location).where(location_id == Location.id)
    result = await session.execute(query)
    location: Location = result.scalars().first()
    return location


async def create_location(name: str, status: LocationStatus, prefab:str,
                          sensor_selected: list[int],session: AsyncSession) -> Location:
    new_location = Location(name=name, status=status, prefab=prefab)
    session.add(new_location)
    await session.flush()
    location_model = [
        {"location_id": new_location.id, "sensor_id": sensor_id}
        for sensor_id in sensor_selected
    ]
    await session.execute(insert(sensor_location_association).values(location_model))
    await session.commit()
    return new_location

async def delete_all_connection_location_model(session: AsyncSession, location_id: int) -> None:
    try:
        query = delete(sensor_location_association).where(sensor_location_association.c.location_id == location_id)
        await session.execute(query)
        await session.commit()
    except Exception as e:
        raise Exception(f"An error occurred while deleting connections: {e}")


async def update_location(location: Location, status: LocationStatus, name: str, prefab: str,
                          sensor_selected: list[int], session: AsyncSession) -> None:
    location.status = status
    location.name = name
    location.prefab = prefab
    session.add(location)
    location_model = [
        {"location_id": location.id, "sensor_id": sensor_id}
        for sensor_id in sensor_selected
    ]
    await session.execute(insert(sensor_location_association).values(location_model))
    await session.commit()


async def get_locations_list(session: AsyncSession) -> Sequence[Location]:
    query = select(Location)
    result = await session.execute(query)
    location_results = result.scalars().all()
    return location_results