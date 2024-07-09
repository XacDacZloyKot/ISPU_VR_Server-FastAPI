import contextlib
import os
from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from fastapi import Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import auth_backend, get_jwt_strategy, current_user
from src.auth.manager import get_user_manager
from src.auth.models import User
from src.auth.utils import get_user_db
from src.database import get_async_session
from src.sensor.models import Model


router = APIRouter(
    prefix='/pages',
    tags=['Pages']
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates\\")


templates = Jinja2Templates(directory=TEMPLATES_DIR)


get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def authenticate(email: str, password: str):
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.authenticate(
                        credentials=OAuth2PasswordRequestForm(username=email, password=password)
                    )
                    response: Response = await auth_backend.login(strategy=get_jwt_strategy(), user=user)
                    print(f"User auth {user}")
                    print(f"Response {response}")
                    return user
    except Exception as e:
        print(e)


@router.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("/login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def post_login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = await authenticate(email=email, password=password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Failed to login"})

    token = await get_jwt_strategy().write_token(user)
    response = RedirectResponse(url="/pages/models/", status_code=302)
    response.set_cookie(key="user-cookie", value=token, httponly=True)
    return response


@router.get("/models/", response_class=HTMLResponse)
async def get_models(request: Request, user: User = Depends(current_user),
                     session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(Model)
        result = await session.execute(query)
        models = result.scalars().all()
        return templates.TemplateResponse("models.html", {"request": request, "models": models,
                                                          'status': HTTPStatus.OK, 'detail': None})
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
    except Exception as e:
        print(e)
        return templates.TemplateResponse("login.html", {"request": request, "error": "Please login first"})


@router.post("/models/", response_class=HTMLResponse, dependencies=[Depends(get_async_session)])
async def create_model(
    sensor_type: str = Form(...),
    specification: str = Form(...),
    parameters: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
):
    # TODO: ПЕРЕДЕЛАТЬ СОЗДАНИЕ
    # new_model = Model(sensor_type=sensor_type, specification=specification, parameters=parameters)
    # session.add(new_model)
    await session.commit()
    return RedirectResponse(url="/pages/models", status_code=303)


@router.post("/models/{id}/", response_class=HTMLResponse, dependencies=[Depends(get_async_session)])
async def delete_model(
    id: int,
    session: AsyncSession = Depends(get_async_session),
):
    query = delete(Model).where(Model.id == id)
    result = await session.execute(query)
    await session.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    return RedirectResponse(url="/pages/models", status_code=303)
