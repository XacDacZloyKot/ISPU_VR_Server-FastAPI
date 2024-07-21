import os
from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from fastapi import Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import get_jwt_strategy, current_user, staff_user, administrator_user
from src.auth.models import User, Admission
from src.database import get_async_session
from src.pages.utils import authenticate, authenticate_for_username, user_menu, create
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


@router.get("/registration", response_class=HTMLResponse)
async def get_registration(request: Request):
    return templates.TemplateResponse("/auth/registration.html", {"request": request})


@router.post("/registration", response_class=HTMLResponse)
async def post_registration(request: Request,
                            username: str = Form(...),
                            password: str = Form(...),
                            first_name: str = Form(...),
                            last_name: str = Form(...),
                            patronymic: str = Form(...),
                            division: str = Form(...)):
    user = await create(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        patronymic=patronymic,
        division=division
    )
    if not user:
        return templates.TemplateResponse("/auth/registration.html", {"request": request, "error": "Error registering user"})
    response = RedirectResponse(url="/pages/loginUser/", status_code=302)
    return response


@router.get("/location", response_class=HTMLResponse)
async def get_location_page(request: Request, user: User = Depends(current_user),
                            session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(Location).order_by(Location.id)
        result = await session.execute(query)
        location = result.scalars().all()
        return templates.TemplateResponse(
            "/location/location.html",
            {
                "request": request,
                'user': user,
                "locations": location,
                'title': "ISPU - Location",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
    except Exception as e:
        print(e)
        return templates.TemplateResponse("/auth/loginAdmin.html", {"request": request, "error": "Please login first"})


@router.get("/home", response_class=HTMLResponse)
async def get_home_page(request: Request, user: User = Depends(current_user),
                        session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(Admission).where(user.id == Admission.user_id)
        result = await session.execute(query)
        admission = result.scalars().all()
        sum_rating = await Admission.get_average_rating_for_user(user_id=user.id, session=session)
        return templates.TemplateResponse(
            "/profile/home.html",
            {
                "request": request,
                'user': user,
                "admissions": admission,
                'title': "ISPU - Home page!",
                'menu': user_menu,
                'sum_rating': sum_rating,
        }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
    except Exception as e:
        print(e)
        return templates.TemplateResponse("/profile/home.html", {"request": request, "error": "Please login first"})


@router.get("/users", response_class=HTMLResponse)
async def get_users_page(request: Request, user: User = Depends(staff_user),
                        session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(User).where(False == User.is_superuser, False == User.is_staff)
        result = await session.execute(query)
        users = result.scalars().all()
        return templates.TemplateResponse(
            "/staff/user.html",
            {
                "request": request,
                'user': user,
                "users": users,
                'title': "ISPU - Users",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
    except Exception as e:
        print(e)
        return templates.TemplateResponse("/profile/home.html", {"request": request, "error": "Please login first"})


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
