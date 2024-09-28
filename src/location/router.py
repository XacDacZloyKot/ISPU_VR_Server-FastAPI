from http import HTTPStatus

from fastapi import APIRouter, Form
from fastapi import Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import staff_user, administrator_user
from src.auth.models import User
from src.database import get_async_session
from src.location.crud import get_location_for_id as get_location_for_id_func, create_location, get_locations, \
    delete_all_connection_location_model, update_location
from src.pages.router import templates
from src.pages.utils import (user_menu,
                             )
from src.sensor import LocationStatus, Location, sensor_location_association
from src.sensor.crud import get_sensors

router = APIRouter(
    prefix='/pages/locations123213',
    tags=['Location']
)


@router.get("/location/{location_id}", response_class=HTMLResponse)
async def get_location_for_id(request: Request, location_id: int, user: User = Depends(staff_user),
                                   session: AsyncSession = Depends(get_async_session)):
    try:
        location = await get_location_for_id_func(location_id=location_id, session=session)
        return templates.TemplateResponse(
            "/location/location_info.html",
            {
                "request": request,
                'user': user,
                "location": location,
                'title': f"ISPU - Профиль пользователя {user.username}!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в локации по id: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'error': "Возникла ошибка с БД при переходе на страницу с локацией.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в локации по id: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'error': "Возникла ошибка при переходе на страницу с локацией.",
            'user': user,
            'menu': user_menu
        })


@router.get("/create/sensor/", response_class=HTMLResponse)
async def get_create_location(request: Request,
                              user: User = Depends(administrator_user),
                              session: AsyncSession = Depends(get_async_session)):
    try:
        sensors = await get_sensors(session=session)
        return templates.TemplateResponse(
            "/staff/create/location/create_location.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'sensors_options': sensors,
                'status_options': LocationStatus,
                'title': "ISPU - Создание локации!",
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в странице создания локации: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка с БД при создании локации.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в странице создания локации: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при создании локации.",
            'user': user,
            'menu': user_menu
        })


@router.post("/location/create/", response_class=HTMLResponse)
async def post_create_location(request: Request,
                               sensor_selected: list[int] = Form(None),
                               name: str = Form(...), prefab: str = Form(...),
                               status: LocationStatus = Form(...),
                               user: User = Depends(administrator_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
        if not sensor_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали приборы для локации.",
                'user': user,
                'menu': user_menu
            })

        location = await create_location(session=session, name=name, prefab=prefab,
                                         sensor_selected=sensor_selected, status=status)
        if not location:
            raise SQLAlchemyError("Ошибка при создании локации")
        return RedirectResponse(url=request.url_for("get_location_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при создания локации: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при создания локации: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


@router.get("/", response_class=HTMLResponse)
async def get_location_page(request: Request, user: User = Depends(staff_user),
                            session: AsyncSession = Depends(get_async_session)):
    try:
        locations = await get_locations(session=session)
        return templates.TemplateResponse(
            "/location/location.html",
            {
                'request': request,
                'user': user,
                "locations": locations,
                'title': "ISPU - Локации",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка на странице с локациями: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка с БД на странице с локациями.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка на странице с локациями: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка на странице с локациями.",
            'user': user,
            'menu': user_menu
        })


@router.get("/update/{location_id}", response_class=HTMLResponse)
async def get_update_location(request: Request, location_id: int, user: User = Depends(administrator_user),
                              session: AsyncSession = Depends(get_async_session)):
    try:
        location: Location = await get_location_for_id_func(session=session, location_id=location_id)
        sensors = await get_sensors(session=session)
        return templates.TemplateResponse(
            "/staff/update/location/update_location.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'sensors_options': sensors,
                'location': location,
                'sensor_in_location': location.sensors,
                'status_options': LocationStatus,
                'title': "ISPU - Создание локации!",
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в странице обновления локации: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении локации.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в странице обновления локации: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении локации.",
            'user': user,
            'menu': user_menu
        })


@router.post("/create/{location_id}", response_class=HTMLResponse)
async def post_update_location(request: Request, location_id: int, sensor_selected: list[int] = Form(None),
                               name: str = Form(...), prefab: str = Form(...), status: LocationStatus = Form(...),
                               user: User = Depends(administrator_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
        if not sensor_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали прибор КИП для локации.",
                'user': user,
                'menu': user_menu
            })

        location = await get_location_for_id_func(session=session, location_id=location_id)
        await delete_all_connection_location_model(session=session, location_id=location_id)
        await update_location(location=location, status=status, name=name, prefab=prefab,
                              sensor_selected=sensor_selected, session=session)
        return RedirectResponse(url=request.url_for("get_location_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при обновления локации: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении локации.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при обновления локации: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении локации.",
            'user': user,
            'menu': user_menu
        })
