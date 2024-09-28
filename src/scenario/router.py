from fastapi import APIRouter, Form, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from http import HTTPStatus

from src.auth.base_config import staff_user, administrator_user, current_user
from src.auth.models import User, Scenario
from src.database import get_async_session
from src.pages.router import templates
from src.pages.utils import (user_menu,
                             )
from src.scenario.crud import get_scenario_for_id as get_scenario_for_id_func, create_scenario, get_scenarios, \
    delete_all_connection_scenario_accident, update_scenario, delete_accident, add_accidents_for_scenario
from src.location.crud import get_location_for_id as get_location_for_id_func, get_locations as get_locations_func
from src.sensor.crud import get_sensor_for_id as get_sensor_for_id_func

router = APIRouter(
    prefix='/pages/scenarios123',
    tags=['Scenario']
)


@router.get("/id/{scenario_id}", response_class=HTMLResponse)
async def get_scenario_for_id(request: Request, scenario_id: int, user: User = Depends(staff_user),
                              session: AsyncSession = Depends(get_async_session)):
    try:
        scenarios = await get_scenario_for_id_func(scenario_id=scenario_id, session=session)
        return templates.TemplateResponse(
            "/staff/get/scenario/scenario_info.html",
            {
                'request': request,
                'user': user,
                'scenarios': scenarios,
                'title': "ISPU - Сценарии!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при выводе сценария по ID: {e}")
        return templates.TemplateResponse("profile/index.html", {
            'request': request,
            'error': "Ошибка при выводе сценария по ID.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при выводе сценария по ID: {e}")
        return templates.TemplateResponse("profile/index.html", {
            'request': request,
            'error': "Ошибка при выводе сценария по ID.",
            'user': user,
            'menu': user_menu
        })


@router.get("/create", response_class=HTMLResponse)
async def get_create_scenario(request: Request, user: User = Depends(administrator_user),
                              session: AsyncSession = Depends(get_async_session)):
    try:
        locations = await get_locations_func(session=session)
        return templates.TemplateResponse(
            "/staff/create/scenario/choice_location.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Создание сценария!",
                'locations': locations,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при выборе локации для сценария: {e}")
        return templates.TemplateResponse("profile/index.html", {
            'request': request,
            'error': "Ошибка при выборе локации при создании сценария.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            'error': f"Ошибка при выборе локации при создании сценария. {e}",
            'request': request,
            'user': user,
            'menu': user_menu
        })


@router.post("/create/model/", response_class=HTMLResponse)
async def get_choice_model_for_scenario(request: Request, location_selected: int = Form(None),
                                        user: User = Depends(administrator_user),
                                        session: AsyncSession = Depends(get_async_session)):
    try:
        if not location_selected:
            return templates.TemplateResponse("profile/index.html", {
                'request': request,
                'error': "Вы не выбрали локацию!",
                'user': user,
                'menu': user_menu
            })
        location = await get_location_for_id_func(session=session, location_id=location_selected)
        sensors = location.sensors
        if not sensors:
            return templates.TemplateResponse("profile/index.html", {
                'request': request,
                'error': "В этой локации нету приборов!",
                'user': user,
                'menu': user_menu
            })
        return templates.TemplateResponse(
            "/staff/create/scenario/choice_model.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Создание сценария!",
                'location_selected': location_selected,
                'sensor_options': sensors,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при выборе модели для сценария: {e}")
        return templates.TemplateResponse("profile/index.html", {
            'request': request,
            'error': "Возникла ошибка с БД при выборе модели для сценария.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при выборе модели для сценария: {e}")
        return templates.TemplateResponse("profile/index.html", {
            'request': request,
            'error': "Возникла ошибка при выборе модели для сценария.",
            'user': user,
            'menu': user_menu
        })


@router.post("/create/accident/{location_selected}", response_class=HTMLResponse)
async def get_choice_accident_for_scenario(request: Request, location_selected: int,
                                           sensor_selected: int = Form(None),
                                           user: User = Depends(administrator_user),
                                           session: AsyncSession = Depends(get_async_session)):
    try:
        if not sensor_selected:
            return templates.TemplateResponse("profile/index.html", {
                'request': request,
                'error': "Вы не выбрали прибора КИП!",
                'user': user,
                'menu': user_menu
            })
        sensor = await get_sensor_for_id_func(session=session, sensor_id=sensor_selected)
        return templates.TemplateResponse(
            "/staff/create/scenario/choice_accident.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Создание сценария!",
                'location_selected': location_selected,
                'sensor_selected': sensor_selected,
                'accidents_options': sensor.model.accidents,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при выборе аварий для сценария: {e}")
        return templates.TemplateResponse("profile/index.html", {
            'request': request,
            'error': "Возникла ошибка с БД при выборе аварий для сценария.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при выборе аварии для сценария: {e}")
        return templates.TemplateResponse("profile/index.html", {
            'request': request,
            'error': "Возникла ошибка при выборе аварий для сценария.",
            'user': user,
            'menu': user_menu
        })


@router.post("/create/{location_id}/{sensor_id}", response_class=HTMLResponse)
async def post_create_scenario(request: Request, location_id: int, sensor_id: int,
                               accident_selected: list[int] = Form(None), name: str = Form(max_length=255),
                               user: User = Depends(administrator_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
        if not accident_selected:
            return templates.TemplateResponse("profile/index.html", {
                'request': request,
                'error': "Вы не выбрали аварию!",
                'user': user,
                'menu': user_menu
            })
        scenario = await create_scenario(location_id=location_id, sensor_id=sensor_id, name=name,
                                         session=session, accident_selected=accident_selected)
        if not scenario:
            return templates.TemplateResponse("profile/index.html", {
                'request': request,
                'error': "Ошибка при создании сценария",
                'user': user,
                'menu': user_menu
            })
        return RedirectResponse(url=request.url_for("get_scenario_for_id", scenario_id=scenario.id),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при создании сценария: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            'request': request,
            'error': "Возникла ошибка с БД при создании сценария.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при создании сценария: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            'request': request,
            'error': "Возникла ошибка при создании сценария.",
            'user': user,
            'menu': user_menu
        })


@router.get("/", response_class=HTMLResponse)
async def get_scenario(request: Request, user: User = Depends(staff_user),
                       session: AsyncSession = Depends(get_async_session)):
    try:
        scenarios = await get_scenarios(session=session)
        return templates.TemplateResponse(
            "/staff/get/scenario/scenario.html",
            {
                'request': request,
                'user': user,
                "scenarios": scenarios,
                'title': "ISPU - Сценарии",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в странице сценариев: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка в странице со сценариями.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в странице сценариев: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка в странице со сценариями.",
            'user': user,
            'menu': user_menu
        })


@router.get("/update/{scenario_id}", response_class=HTMLResponse)
async def get_update_scenario(request: Request, scenario_id: int,
                              user: User = Depends(administrator_user),
                              session: AsyncSession = Depends(get_async_session)):
    try:
        scenario = await get_scenario_for_id_func(session=session, scenario_id=scenario_id)
        locations = await get_locations_func(session=session)
        return templates.TemplateResponse(
            "/staff/update/scenario/choice_location.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Обновление сценария!",
                'locations': locations,
                'scenario': scenario,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в странице обновления сценария: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла проблема при обновлении сценария.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в странице обновления сценария: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла проблема при обновлении сценария.",
            'user': user,
            'menu': user_menu
        })


@router.post("/update/model/{scenario_id}", response_class=HTMLResponse)
async def get_choice_sensor_for_update_scenario(request: Request, scenario_id: int,
                                                location_selected: int = Form(None),
                                                user: User = Depends(administrator_user),
                                                session: AsyncSession = Depends(get_async_session)):
    try:
        if not location_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали локацию!",
                'user': user,
                'menu': user_menu
            })
        scenario = await get_scenario_for_id_func(session=session, scenario_id=scenario_id)
        location = await get_location_for_id_func(session=session, location_id=location_selected)
        is_changed = False
        if scenario.location.id == location.id:
            is_changed = True
        return templates.TemplateResponse(
            "/staff/update/scenario/choice_sensor.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Обновление сценария!",
                'location_selected': location_selected,
                'scenario': scenario,
                'sensor_options': location.sensors,
                'is_changed': is_changed,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy возникла ошибка при обновлении сценария(get_choice_sensor_for_update_scenario): {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при обновлении сценария.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Возникла ошибка при обновлении сценария(get_choice_sensor_for_update_scenario): {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при обновлении сценария.",
            'user': user,
            'menu': user_menu
        })


@router.post("/update/accident/{scenario_id}", response_class=HTMLResponse)
async def get_choice_accident_for_update_scenario(request: Request, scenario_id: int,
                                                  location_selected: int = Form(...),
                                                  sensor_selected: int = Form(None),
                                                  user: User = Depends(administrator_user),
                                                  session: AsyncSession = Depends(get_async_session)):
    try:
        if not sensor_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали прибора КИП для сценария.",
                'user': user,
                'menu': user_menu
            })
        scenario = await get_scenario_for_id_func(session=session, scenario_id=scenario_id)
        sensor = await get_sensor_for_id_func(session=session, sensor_id=sensor_selected)
        is_changed = False
        if scenario.sensor.id == sensor.id:
            is_changed = True
        return templates.TemplateResponse(
            "/staff/update/scenario/choice_accident.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Обновление сценария!",
                'location_selected': location_selected,
                'sensor_selected': sensor_selected,
                'scenario': scenario,
                'accidents_options': sensor.model.accidents,
                'is_changed': is_changed,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy возникла ошибка при обновлении сценария(get_choice_accident_for_update_scenario): {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при обновлении сценария.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Возникла ошибка при обновлении сценария(get_choice_accident_for_update_scenario): {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при обновлении сценария.",
            'user': user,
            'menu': user_menu
        })


@router.post("/update/{scenario_id}/", response_class=HTMLResponse)
async def post_update_scenario(request: Request, scenario_id: int, location_selected: int = Form(...),
                               sensor_selected: int = Form(...), accident_selected: list[int] = Form(None),
                               name: str = Form(max_length=255), user: User = Depends(administrator_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
        if not accident_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали аварии для сценария.",
                'user': user,
                'menu': user_menu
            })
        await update_scenario(scenario_id=scenario_id, name=name, sensor=sensor_selected, location=location_selected,
                              accidents=accident_selected, session=session)
        return RedirectResponse(url=request.url_for("get_scenario"), status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy возникла ошибка при обновлении сценария(post_update_scenario): {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при обновлении сценария.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Возникла ошибка при обновлении сценария(post_update_scenario): {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при обновлении сценария.",
            'user': user,
            'menu': user_menu
        })


@router.post("/accident/delete/{accident_id}/{scenario_id}")
async def delete_accident_for_scenario(accident_id: int, scenario_id: int,
                                            session: AsyncSession = Depends(get_async_session),
                                            user: User = Depends(administrator_user)):
    try:
        await delete_accident(session=session, scenario_id=scenario_id, accident_id=accident_id)
        return {'status': HTTPStatus.OK, 'detail': "Accident deleted successfully"}
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при удалении ошибки в сценарии: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        print(f"Ошибка при удалении ошибки в сценарии: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/accident/add/{scenario_id}", response_class=HTMLResponse)
async def get_add_accident_scenario(
        request: Request,
        scenario_id: int,
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        scenario: Scenario = await get_scenario_for_id_func(scenario_id=scenario_id, session=session)
        return templates.TemplateResponse(
            "/staff/update/accident/add_accident_scenario.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Добавление аварии!",
                'scenario_accidents': scenario.accidents,
                'model_accidents': scenario.sensor.model.accidents,
                'scenario': scenario,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в странице добавления аварии: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при добавлении аварии.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в странице добавления аварии: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'user': user,
            "error": "Возникла ошибка при добавлении аварии.",
            'menu': user_menu
        })


@router.post("/accident/add/{scenario_id}", response_class=HTMLResponse)
async def post_add_accident_scenario(
        request: Request,
        scenario_id: int,
        accidents_selected: list[int] = Form(None),
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        if not accidents_selected:
            raise Exception("Не выбраны аварии")

        await delete_all_connection_scenario_accident(session=session, scenario_id=scenario_id)
        await add_accidents_for_scenario(session=session, accidents_id=accidents_selected, scenario_id=scenario_id)
        return RedirectResponse(request.url_for("get_scenario_for_id", scenario_id=scenario_id),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)

    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при добавления аварии: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'user': user,
            "error": "Возникла ошибка при добавлении аварии.",
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при добавления аварии: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при добавлении аварии.",
            'user': user,
            'menu': user_menu
        })
