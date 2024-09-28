from http import HTTPStatus

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import staff_user, administrator_user
from src.auth.models import User
from src.database import get_async_session
from src.pages.router import templates
from src.pages.utils import (user_menu,
                             )
from src.sensor.crud import get_sensor_for_id as get_sensor_for_id_func, create_sensor as create_sensor_func, \
    get_sensors, update_sensor
from src.model.crud import get_models

router = APIRouter(
    prefix='/pages/sensors12321',
    tags=['Sensor']
)


@router.get("/id/{sensor_id}", response_class=HTMLResponse)
async def get_sensor_for_id(request: Request, sensor_id: int, user: User = Depends(staff_user),
                            session: AsyncSession = Depends(get_async_session)):
    try:
        sensor = await get_sensor_for_id_func(sensor_id=sensor_id, session=session)
        return templates.TemplateResponse(
            "/location/sensor_info.html",
            {
                "request": request,
                'user': user,
                "sensor": sensor,
                'title': f"ISPU - Прибор КИП #{sensor_id}!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка страницы прибора КИП по id: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'error': "Возникла ошибка при переходе на страницу с прибором.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка страницы прибора КИП по id: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'error': "Возникла ошибка при переходе на страницу с прибором.",
            'user': user,
            'menu': user_menu
        })

@router.get("/create/", response_class=HTMLResponse)
async def get_create_sensor(request: Request, user: User = Depends(administrator_user),
                            session: AsyncSession = Depends(get_async_session)):
    try:
        models = await get_models(session=session)
        return templates.TemplateResponse(
            "/staff/create/sensor/create_sensor.html",
            {
                "request": request,
                'user': user,
                "models": models,
                'title': "ISPU - Создиние прибора КИП!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка страницы создания прибора КИП: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'error': "Возникла ошибка при переходе на страницу для создания прибора.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка страницы создания прибора КИП: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'error': "Возникла ошибка при переходе на страницу для создания прибора.",
            'user': user,
            'menu': user_menu
        })

@router.post("/create/", response_class=HTMLResponse)
async def post_create_sensor(request: Request, selected_model: int = Form(None),
                             name: str = Form(...), KKS: str = Form(...),
                             current_user: User = Depends(administrator_user),
                             session: AsyncSession = Depends(get_async_session)):
    try:
        if not selected_model:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали модель для прибора КИП!",
                'user': current_user,
                'menu': user_menu
            })
        await create_sensor_func(session=session, model_id=selected_model, name=name, KKS=KKS)
        return RedirectResponse(url=request.url_for("get_sensor_page"),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при создания прибора КИП: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка создания прибора КИП.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при создания прибора КИП: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка создания прибора КИП.",
            'user': current_user,
            'menu': user_menu
        })


@router.get("/", response_class=HTMLResponse)
async def get_sensor_page(request: Request, user: User = Depends(staff_user),
                          session: AsyncSession = Depends(get_async_session)):
    try:
        sensors = await get_sensors(session=session)
        return templates.TemplateResponse(
            "/location/sensors.html",
            {
                'request': request,
                'user': user,
                "sensors": sensors,
                'title': "ISPU - Прибор КИП",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка на странице с приборами КИП: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка на странице с приборами КИП",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка на странице с приборами КИП: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка на странице с приборами КИП",
            'user': user,
            'menu': user_menu
        })


@router.get("/update/{sensor_id}", response_class=HTMLResponse)
async def get_update_sensor(request: Request, sensor_id: int, user: User = Depends(administrator_user),
                            session: AsyncSession = Depends(get_async_session)):
    try:
        models = await get_models(session=session)
        sensor = await get_sensor_for_id_func(session=session, sensor_id=sensor_id)
        return templates.TemplateResponse(
            "/staff/update/sensor/update_sensor.html",
            {
                'request': request,
                'user': user,
                'models': models,
                'sensor': sensor,
                'title': "ISPU - Обновление прибора КИП!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в странице обновления прибора КИП: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении прибора КИП.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в странице обновления прибора КИП: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении прибора КИП.",
            'user': user,
            'menu': user_menu
        })


@router.post("/update/{sensor_id}", response_class=HTMLResponse)
async def post_update_sensor(request: Request, sensor_id: int, selected_model: int = Form(None),
                             name: str = Form(...), KKS: str = Form(...),
                             user: User = Depends(administrator_user),
                             session: AsyncSession = Depends(get_async_session)):
    try:
        if not selected_model:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали модель для прибора КИП.",
                'user': user,
                'menu': user_menu
            })
        sensor = await get_sensor_for_id_func(session=session, sensor_id=sensor_id)
        await update_sensor(model_id=selected_model, KKS=KKS, name=name, sensor=sensor, session=session)

        return RedirectResponse(url=request.url_for("get_sensor_page"),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при обновлении прибора КИП: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении прибора КИП.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при обновлении прибора КИП: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении прибора КИП.",
            'user': user,
            'menu': user_menu
        })