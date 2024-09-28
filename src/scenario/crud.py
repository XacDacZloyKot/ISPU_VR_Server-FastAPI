from sqlalchemy import select, insert, Sequence, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import Scenario
from src.sensor import scenario_accident_association, Location, LocationStatus


async def get_scenario_for_id(scenario_id: int, session: AsyncSession) -> Scenario:
    try:
        query = select(Scenario).where(scenario_id == Scenario.id)
        result = await session.execute(query)
        scenario: Scenario = result.scalars().first()
        return scenario
    except SQLAlchemyError as e:
        print(f"SQLAlchemyError ошибка при получении сценария по ID: {e} {e.code}")
        raise SQLAlchemyError("Ошибка SQLAlchemyError при получении сценария по ID")


async def create_scenario(location_id: int, sensor_id: int, name: str,
                          accident_selected: list[int], session: AsyncSession) -> Scenario:
    new_scenario = Scenario(location_id=location_id, sensor_id=sensor_id, name=name)
    session.add(new_scenario)
    await session.flush()
    scenario_accidents = [
        {"scenario_id": new_scenario.id, "accident_id": accident_id}
        for accident_id in accident_selected
    ]
    await session.execute(insert(scenario_accident_association).values(scenario_accidents))
    await session.commit()
    return new_scenario


async def get_active_scenarios(session: AsyncSession) -> Sequence[Scenario]:
    query = (
        select(Scenario)
        .join(Location)
        .where(LocationStatus.COMPLETED == Location.status)
    )
    result = await session.execute(query)
    scenarios = result.scalars().all()

    return scenarios


async def get_scenarios(session: AsyncSession) -> Sequence[Scenario]:
    query = select(Scenario).order_by(Scenario.id)
    result = await session.execute(query)
    scenarios = result.scalars().all()
    return scenarios

async def delete_all_connection_scenario_accident(session: AsyncSession, scenario_id: int) -> None:
    try:
        query = delete(scenario_accident_association).where(scenario_accident_association.c.scenario_id == scenario_id)
        await session.execute(query)
        await session.commit()
    except Exception as e:
        raise Exception(f"An error occurred while deleting connections: {e}")


async def update_scenario(scenario_id: int, name: str, sensor: int,
                          location: int, accidents: list[int], session: AsyncSession) -> None:
    scenario = await get_scenario_for_id(scenario_id=scenario_id, session=session)
    await delete_all_connection_scenario_accident(session=session, scenario_id=scenario_id)
    scenario.name = name
    scenario.sensor_id = sensor
    scenario.location_id = location
    session.add(scenario)
    sensor_accident = [
        {"scenario_id": scenario.id, "accident_id": accident_id}
        for accident_id in accidents
    ]
    await session.execute(insert(scenario_accident_association).values(sensor_accident))
    await session.commit()


async def delete_accident(session: AsyncSession, scenario_id: int, accident_id: int) -> None:
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