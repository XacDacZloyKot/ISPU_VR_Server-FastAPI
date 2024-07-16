import os
from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from fastapi import Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.pages.utils import authenticate, authenticate_for_username
from src.auth.base_config import get_jwt_strategy, current_user
from src.auth.models import User
from src.database import get_async_session
from src.sensor.models import Model, Location

router = APIRouter(
    prefix='/pages',
    tags=['Pages']
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates\\")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/loginAdmin", response_class=HTMLResponse)
async def get_login_admin(request: Request):
    return templates.TemplateResponse("/auth/loginAdmin.html", {"request": request})


@router.post("/loginAdmin", response_class=HTMLResponse)
async def post_login_admin(request: Request, email: str = Form(...), password: str = Form(...)):
    user = await authenticate(email=email, password=password)
    if not user:
        return templates.TemplateResponse("/auth/loginAdmin.html", {"request": request, "error": "Failed to login"})

    token = await get_jwt_strategy().write_token(user)
    response = RedirectResponse(url="/pages/location/", status_code=302)
    response.set_cookie(key="user-cookie", value=token, httponly=True)
    return response


@router.get("/loginUser", response_class=HTMLResponse)
async def get_login_user(request: Request):
    return templates.TemplateResponse("/auth/loginUser.html", {"request": request})


@router.post("/loginUser", response_class=HTMLResponse)
async def post_login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    user = await authenticate_for_username(username=username, password=password)
    if not user:
        return templates.TemplateResponse("/auth/loginUser.html", {"request": request, "error": "Failed to login"})

    token = await get_jwt_strategy().write_token(user)
    response = RedirectResponse(url="/pages/location/", status_code=302)
    response.set_cookie(key="user-cookie", value=token, httponly=True)
    return response


@router.get("/location", response_class=HTMLResponse)
async def get_location(request: Request, user: User = Depends(current_user),
                       session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(Location).order_by(Location.id)
        result = await session.execute(query)
        location = result.scalars().all()
        return templates.TemplateResponse(
            "/location/location.html",
            {
                "request": request,
                "locations": location,
                'status': HTTPStatus.OK,
                'user': user,
                'title': "ISPU - Location"
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
    except Exception as e:
        print(e)
        return templates.TemplateResponse("/auth/loginAdmin.html", {"request": request, "error": "Please login first"})


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
        return templates.TemplateResponse("/auth/loginAdmin.html", {"request": request, "error": "Please login first"})


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
    query = delete(Model).where(id == Model.id)
    result = await session.execute(query)
    await session.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    return RedirectResponse(url="/pages/models", status_code=303)
