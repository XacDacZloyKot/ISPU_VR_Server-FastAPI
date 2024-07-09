from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from http import HTTPStatus

from src.sensor.schemas import ModelResponse
from src.auth.base_config import current_user
from src.auth.models import User
from src.database import get_async_session
from src.sensor.models import Model


router = APIRouter(
    prefix="/models",
    tags=["Sensor"]
)


@router.get("/")
async def get_models(session: AsyncSession = Depends(get_async_session)):
    query = select(Model)
    result = await session.execute(query)
    rows = result.mappings().all()
    return {'status': HTTPStatus.OK, 'data': rows, 'details': None}


@router.get("/{sensor_type}")
async def get_type_models(sensor_type: str, session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(Model).where(Model.c.sensor_type == sensor_type)
        result = await session.execute(query)
        rows = result.mappings().all()
        return {'status': HTTPStatus.OK, 'data': rows, 'details': None}
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail={'data': None, 'details': str(e)})


@router.post("/")
async def add_models(new_model: ModelResponse, session: AsyncSession = Depends(get_async_session)):
    try:
        stmt = insert(Model).values(**new_model.dict())
        await session.execute(stmt)
        await session.commit()
        return {'status': HTTPStatus.OK, 'data': new_model, 'details': None}
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail={'data': None, 'details': str(e)})


@router.get("/protected-route/")
def protected_route(user: User = Depends(current_user)):
    print(user)
    return f"Hello, {user.username}"


@router.get("/unprotected-route/")
def unprotected_route():
    return f"Hello, anonym"