import os
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi import Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select, insert, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import get_jwt_strategy, current_user, staff_user, administrator_user
from src.auth.models import User, Admission, AdmissionStatus, Scenario
from src.database import get_async_session
from src.pages.crud import (
    get_admission_for_user_id,
    get_user_for_id,
    get_scenario_for_id,
    get_users_without_scenario,
    get_admission_for_id, get_name_sensor_value, get_sensor_value_for_name, get_sensor_values_for_id,
    create_or_get_sensor_type, get_all_models, get_location_list, get_location_for_id,
    get_sensor_for_id, get_model_for_id, get_all_sensors, get_scenarios_active_list, get_all_sensor_types,
    delete_all_connection_location_model, delete_all_connection_scenario_accident, delete_accident_for_scenario,
    delete_accident_for_model, add_accidents_for_scenario, create_sensor,
)
from src.pages.utils import (authenticate,
                             authenticate_for_username,
                             user_menu,
                             create,
                             get_last_admission_task,
                             logout as logout_func, create_json_scenario, start_app,
                             )
from src.sensor.models import scenario_accident_association, Model, Accident, model_accident_association, Location, \
    LocationStatus, sensor_location_association

router = APIRouter(
    prefix='/pages',
    tags=['Pages']
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates\\")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/", response_class=HTMLResponse)
async def index_page(request: Request, user=Depends(current_user)):
    return templates.TemplateResponse("/profile/index.html", {
        "request": request,
        'user': user,
        'menu': user_menu,
        'title': "ISPU - Главная страница!"
    })


@router.get("/loginAdmin", response_class=HTMLResponse)
async def get_login_admin(request: Request):
    return templates.TemplateResponse("/auth/loginAdmin.html", {"request": request})


@router.post("/loginAdmin", response_class=HTMLResponse)
async def post_login_admin(request: Request, email: str = Form(...), password: str = Form(...)):
    user = await authenticate(email=email, password=password)
    if not user:
        return templates.TemplateResponse("/auth/loginAdmin.html", {"request": request, "error": "Failed to login"})

    token = await get_jwt_strategy().write_token(user)
    response = RedirectResponse(url=request.url_for("index_page"), status_code=302)
    response.set_cookie(key="user-cookie", value=token, httponly=True, path="/")
    return response


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request, user=Depends(current_user)):
    redirect_response = RedirectResponse(url=request.url_for("get_login_user"), status_code=302)
    response_cookie = await logout_func(request=request, user=user, response=redirect_response)
    return response_cookie


@router.get("/loginUser", response_class=HTMLResponse)
async def get_login_user(request: Request):
    return templates.TemplateResponse("/auth/loginUser.html", {"request": request})


@router.post("/loginUser", response_class=HTMLResponse)
async def post_login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    user = await authenticate_for_username(username=username, password=password)
    if not user:
        return templates.TemplateResponse("/auth/loginUser.html", {"request": request, "error": "Failed to login"})

    token = await get_jwt_strategy().write_token(user)
    response = RedirectResponse(url=request.url_for("get_home_page"), status_code=302)
    response.set_cookie(key="user-cookie", value=token, httponly=True, path="/")
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
    try:
        user = await create(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            division=division
        )
        if not user:
            return templates.TemplateResponse("/auth/registration.html", {"request": request,
                                                                          "error": "Неверно введены данные!"})
        response = RedirectResponse(url=request.url_for("post_login_user"), status_code=302)
        return response
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request, "error": "There was some problem"
                                                                                                " with the scripts."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request, "error": "There was some problem"
                                                                                                " with the scripts."})


@router.get("/home", response_class=HTMLResponse)
async def get_home_page(request: Request, user: User = Depends(current_user),
                        session: AsyncSession = Depends(get_async_session)):
    try:
        admission = await get_admission_for_user_id(user_id=user.id, session=session)
        sum_rating = await Admission.get_average_rating_for_user(user_id=user.id, session=session)
        last_admission = get_last_admission_task(list_admission_tasks=admission)
        return templates.TemplateResponse(
            "/profile/home.html",
            {
                "request": request,
                'user': user,
                'admissions': admission,
                'last_admission': last_admission,
                'title': "ISPU - Home page!",
                'menu': user_menu,
                'sum_rating': sum_rating,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse('profile/index.html', {"request": request, "error": "There is some problem "
                                                                                              "with the home page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse('profile/index.html', {"request": request, "error": "There is some problem "
                                                                                              "with the home page."})


# region ID_Page
@router.get("/users/{user_id}", response_class=HTMLResponse)
async def get_profile_for_id_page(request: Request, user_id: int, current_user: User = Depends(staff_user),
                                  session: AsyncSession = Depends(get_async_session)):
    try:
        user = await get_user_for_id(user_id, session)
        admission = await get_admission_for_user_id(user_id, session)
        sum_rating = await Admission.get_average_rating_for_user(user_id=user_id, session=session)
        return templates.TemplateResponse(
            "/profile/profile_user_for_admin.html",
            {
                "request": request,
                'user': current_user,
                "user_for_id": user,
                "sum_rating": sum_rating,
                "admissions": admission,
                'title': "ISPU - User Profile!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the profile page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the profile page.",
            'user': current_user,
            'menu': user_menu
        })


@router.get("/scenarios/{scenario_id}", response_class=HTMLResponse)
async def get_scenario_for_id_page(request: Request, scenario_id: int, user: User = Depends(staff_user),
                                   session: AsyncSession = Depends(get_async_session)):
    try:
        scenarios = await get_scenario_for_id(scenario_id=scenario_id, session=session)
        return templates.TemplateResponse(
            "/location/scenario_info.html",
            {
                'request': request,
                'user': user,
                'scenarios': scenarios,
                'title': "ISPU - Scenario!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There was some problem with the scripts.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There was some problem with the scripts.",
            'user': user,
            'menu': user_menu
        })


@router.get("/location/{location_id}", response_class=HTMLResponse)
async def get_location_for_id_page(request: Request, location_id: int, current_user: User = Depends(staff_user),
                                   session: AsyncSession = Depends(get_async_session)):
    try:
        location = await get_location_for_id(location_id=location_id, session=session)
        return templates.TemplateResponse(
            "/location/location_info.html",
            {
                "request": request,
                'user': current_user,
                "location": location,
                'title': "ISPU - User Profile!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the location page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the location page.",
            'user': current_user,
            'menu': user_menu
        })


@router.get("/sensor/{sensor_id}", response_class=HTMLResponse)
async def get_sensor_for_id_page(request: Request, sensor_id: int, current_user: User = Depends(staff_user),
                                 session: AsyncSession = Depends(get_async_session)):
    try:
        sensor = await get_sensor_for_id(sensor_id=sensor_id, session=session)
        return templates.TemplateResponse(
            "/location/sensor_info.html",
            {
                "request": request,
                'user': current_user,
                "sensor": sensor,
                'title': "ISPU - User Profile!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the sensor page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the sensor page.",
            'user': current_user,
            'menu': user_menu
        })


@router.get("/model/{model_id}", response_class=HTMLResponse)
async def get_model_for_id_page(request: Request, model_id: int, current_user: User = Depends(staff_user),
                                session: AsyncSession = Depends(get_async_session)):
    try:
        model = await get_model_for_id(model_id=model_id, session=session)
        return templates.TemplateResponse(
            "/location/model_info.html",
            {
                "request": request,
                'user': current_user,
                "model": model,
                'title': "ISPU - User Profile!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })


# endregion


@router.get("/scenario/add/{scenario_id}", response_class=HTMLResponse)
async def get_task_assignment(request: Request, scenario_id: int, current_user: User = Depends(staff_user),
                              session: AsyncSession = Depends(get_async_session)):
    try:
        scenario = await get_scenario_for_id(scenario_id=scenario_id, session=session)
        users = await get_users_without_scenario(scenario_id=scenario_id, session=session)
        return templates.TemplateResponse(
            "/staff/assignment_task/add_task_user.html",
            {
                'request': request,
                'user': current_user,
                'users': users,
                'scenario': scenario,
                'title': "ISPU - Assignment task!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the assignment task page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the assignment task page.",
            'user': current_user,
            'menu': user_menu
        })


@router.post("/scenario/add/{scenario_id}", response_class=HTMLResponse)
async def post_task_assignment(request: Request, scenario_id: int, user_ids: list[int] = Form(...),
                               current_user: User = Depends(staff_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
        for user_id in user_ids:
            admission = Admission(status=AdmissionStatus.ACTIVE, user_id=user_id, rating="0", scenario_id=scenario_id)
            session.add(admission)
        await session.commit()
        response = RedirectResponse(url=request.url_for("get_scenario_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
        return response
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the assignment task page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the assignment task page.",
            'user': current_user,
            'menu': user_menu
        })


# region CreateScenario
@router.get("/scenario/create", response_class=HTMLResponse)
async def get_create_scenario_page(request: Request, user: User = Depends(administrator_user),
                                   session: AsyncSession = Depends(get_async_session)):
    try:
        location = await get_location_list(session=session)
        return templates.TemplateResponse(
            "/staff/create/scenario/choice_location.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Create scenario!",
                'location_options': location,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/scenario/create/model/", response_class=HTMLResponse)
async def get_choice_model_for_scenario_page(request: Request, location_selected: int = Form(None),
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
        location = await get_location_for_id(session=session, location_id=location_selected)
        sensors = location.sensors
        return templates.TemplateResponse(
            "/staff/create/scenario/choice_model.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Create scenario!",
                'location_selected': location_selected,
                'sensor_options': sensors,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/scenario/create/accident/{location_selected}", response_class=HTMLResponse)
async def get_choice_accident_for_scenario_page(request: Request, location_selected: int,
                                                sensor_selected: int = Form(None),
                                                user: User = Depends(administrator_user),
                                                session: AsyncSession = Depends(get_async_session)):
    try:
        if not sensor_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали сенсор!",
                'user': user,
                'menu': user_menu
            })
        sensor = await get_sensor_for_id(session=session, sensor_id=sensor_selected)
        return templates.TemplateResponse(
            "/staff/create/scenario/choice_accident.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Create scenario!",
                'location_selected': location_selected,
                'sensor_selected': sensor_selected,
                'accidents_options': sensor.model.accidents,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/scenario/create/{location_id}/{sensor_id}", response_class=HTMLResponse)
async def post_create_scenario(request: Request, location_id: int, sensor_id: int,
                               accident_selected: list[int] = Form(None), name: str = Form(max_length=255),
                               user: User = Depends(administrator_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
        if not accident_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали аварию!",
                'user': user,
                'menu': user_menu
            })
        new_scenario = Scenario(location_id=location_id, sensor_id=sensor_id, name=name)
        session.add(new_scenario)
        await session.flush()
        scenario_accidents = [
            {"scenario_id": new_scenario.id, "accident_id": accident_id}
            for accident_id in accident_selected
        ]
        await session.execute(insert(scenario_accident_association).values(scenario_accidents))
        await session.commit()
        return RedirectResponse(url=request.url_for("get_scenario_for_id_page", scenario_id=new_scenario.id),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the assignment task page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the assignment task page.",
            'user': user,
            'menu': user_menu
        })


# endregion


# region UpdateUser
@router.get("/users/update/{user_id}", response_class=HTMLResponse)
async def get_update_user_page(request: Request, user_id: int, user: User = Depends(staff_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
        current_user = await get_user_for_id(user_id=user_id, session=session)
        return templates.TemplateResponse(
            "/staff/update/user/update_user.html",
            {
                'request': request,
                'user': user,
                'current_user': current_user,
                'menu': user_menu,
                'title': "ISPU - Update user",
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the update user page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the update user page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/users/update/{user_id}/", response_class=HTMLResponse)
async def put_user(request: Request, user_id: int,
                   username=Form(...), first_name=Form(...), last_name=Form(...),
                   patronymic=Form(...), division=Form(...),
                   user: User = Depends(staff_user), session: AsyncSession = Depends(get_async_session)):
    try:
        stmt = update(User).where(User.id == user_id).values(first_name=first_name,
                                                             last_name=last_name,
                                                             patronymic=patronymic,
                                                             division=division,
                                                             username=username)
        await session.execute(stmt)
        await session.commit()

        return RedirectResponse(url=request.url_for("get_users_page"),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the update user page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the update user page.",
            'user': user,
            'menu': user_menu
        })


# endregion


# region UpdateAdmission
@router.get("/admission/update/{admission_id}", response_class=HTMLResponse)
async def get_update_admission_page(
        request: Request,
        admission_id: int,
        error: Optional[str] = None,
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        admission = await get_admission_for_id(admission_id=admission_id, session=session)
        return templates.TemplateResponse(
            "/staff/update/admission/update_admission_for_user.html",
            {
                'request': request,
                'user': user,
                'admission': admission,
                'status_options': AdmissionStatus,
                'menu': user_menu,
                'title': "ISPU - Update admission",
                'error': error
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the update admission page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the update admission page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/admission/update/{admission_id}/", response_class=HTMLResponse)
async def put_admission(
        request: Request,
        admission_id: int,
        rating: str = Form(...),
        status: AdmissionStatus = Form(...),
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        admission: Admission = await get_admission_for_id(admission_id=admission_id, session=session)
        Admission.set_rating(admission, rating)
        admission.status = status
        session.add(admission)
        await session.commit()

        return RedirectResponse(url=request.url_for("get_users_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the update admission page.",
            'user': user,
            'menu': user_menu
        })
    except ValidationError as e:
        error_message = str(e)
        return templates.TemplateResponse("/staff/update/admission/update_admission_for_user.html", {
            "request": request,
            "error": error_message,
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the update admission page.",
            'user': user,
            'menu': user_menu
        })


# endregion


# region DeleteAdmission
@router.delete("/admission/delete/{admission_id}", name="delete_admission")
async def delete_admission(admission_id: int, session: AsyncSession = Depends(get_async_session),
                           user: User = Depends(staff_user)):
    try:
        result = await session.execute(select(Admission).filter_by(id=admission_id))
        admission = result.scalars().first()

        if admission is None:
            raise HTTPException(status_code=404, detail="Admission not found")

        await session.delete(admission)
        await session.commit()

        return {"detail": "Admission deleted successfully"}

    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        print(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


# endregion


# region CreateModel
@router.get("/model/create/sensor/", response_class=HTMLResponse)
async def get_create_model_page(request: Request, user: User = Depends(administrator_user),
                                session: AsyncSession = Depends(get_async_session)):
    try:
        sensor_value_names = await get_name_sensor_value(session=session)
        return templates.TemplateResponse(
            "/staff/create/model/choice_sensor_type.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Create model!",
                'model_options': sensor_value_names,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/model/create/fields/", response_class=HTMLResponse)
async def get_choice_fields(request: Request, model_selected: str = Form(...), user: User = Depends(administrator_user),
                            session: AsyncSession = Depends(get_async_session)):
    try:
        values = await get_sensor_value_for_name(session=session, sensor_name=model_selected)
        return templates.TemplateResponse(
            "/staff/create/model/choice_fields.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Create scenario!",
                'fields_options': values,
                'model_selected': model_selected,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/model/create/{models_name}", response_class=HTMLResponse)
async def create_model(
        request: Request,
        models_name: str,
        fields_selected: list[int] = Form(None),
        user: User = Depends(administrator_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        if not fields_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали параметры модели!",
                'user': user,
                'menu': user_menu
            })
        fields = await get_sensor_values_for_id(session=session, fields_id=fields_selected)
        fields_dict = dict()
        for field in fields:
            fields_dict[field.field] = f"{field.value} {field.measurement}"
        id: int = await create_or_get_sensor_type(session=session, sensor_type_name=models_name)
        new_model = Model(specification=fields_dict, model_type_id=id)
        session.add(new_model)
        await session.commit()
        return RedirectResponse(url=request.url_for("get_add_accident_page", model_id=new_model.id),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })


# endregion


# region CreateSensor
@router.get("/sensor/create/", response_class=HTMLResponse)
async def get_create_sensor_page(request: Request, current_user: User = Depends(administrator_user),
                                 session: AsyncSession = Depends(get_async_session)):
    try:
        models = await get_all_models(session=session)
        return templates.TemplateResponse(
            "/staff/create/sensor/create_sensor.html",
            {
                "request": request,
                'user': current_user,
                "models": models,
                'title': "ISPU - User Profile!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })


@router.post("/sensor/create/", response_class=HTMLResponse)
async def post_update_model_page(request: Request, model_selected: int = Form(None),
                                 name: str = Form(...),
                                 KKS: str = Form(...),
                                 current_user: User = Depends(administrator_user),
                                 session: AsyncSession = Depends(get_async_session)):
    try:
        if not model_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали модель для сенсора!",
                'user': current_user,
                'menu': user_menu
            })
        await create_sensor(session=session, model_id=model_selected, name=name, KKS=KKS)
        return RedirectResponse(url=request.url_for("get_sensor_page"),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the sensor page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the sensor page.",
            'user': current_user,
            'menu': user_menu
        })


# endregion


# region AddAccidentModel
@router.get("/accident/create/{model_id}", response_class=HTMLResponse)
async def get_add_accident_page(
        request: Request,
        model_id: int,
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        model = await get_model_for_id(session=session, model_id=model_id)
        return templates.TemplateResponse(
            "/staff/create/model/add_accident.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Add accident!",
                'model': model,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/accident/create/{model_id}", response_class=HTMLResponse)
async def post_add_accident_page(
        request: Request,
        model_id: int,
        name: str = Form(...),
        mechanical_accident: bool = Form(default=False),
        change_value: str = Form(...),
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        print("post_add_accident_page")
        change_value_dict = {}
        change_value_entries = change_value.split(',')
        for entry in change_value_entries:
            if ':' in entry:
                key, value = entry.split(':', 1)
                change_value_dict[key] = value

        new_accident = Accident(
            name=name,
            mechanical_accident=mechanical_accident,
            change_value=change_value_dict
        )
        session.add(new_accident)
        await session.commit()

        link_model = model_accident_association.insert().values(model_id=model_id, accident_id=new_accident.id)
        await session.execute(link_model)
        await session.commit()

        return RedirectResponse(request.url_for("get_add_accident_page", model_id=model_id),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)

    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })


# endregion


# region CreateLocation
@router.get("/location/create/sensor/", response_class=HTMLResponse)
async def get_create_location_page(request: Request,
                                   user: User = Depends(administrator_user),
                                   session: AsyncSession = Depends(get_async_session)):
    try:
        sensors = await get_all_sensors(session=session)
        return templates.TemplateResponse(
            "/staff/create/location/create_location.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'sensors_options': sensors,
                'status_options': LocationStatus,
                'title': "ISPU - Create scenario!",
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/location/create/", response_class=HTMLResponse)
async def post_create_location_page(request: Request,
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
        new_location = Location(name=name, status=status, prefab=prefab)
        session.add(new_location)
        await session.flush()
        location_model = [
            {"location_id": new_location.id, "sensor_id": sensor_id}
            for sensor_id in sensor_selected
        ]
        await session.execute(insert(sensor_location_association).values(location_model))
        await session.commit()
        return RedirectResponse(url=request.url_for("get_location_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


# endregion


# region AssigmentTaskForUser
@router.get("/scenario/add_user/{user_id}", response_class=HTMLResponse)
async def get_task_assignment_for_curr_user(request: Request, user_id: int, current_user: User = Depends(staff_user),
                                            session: AsyncSession = Depends(get_async_session)):
    try:
        scenarios = await get_scenarios_active_list(session=session)
        return templates.TemplateResponse(
            "/staff/assignment_task/task_for_curr_user.html",
            {
                'request': request,
                'user_id': user_id,
                'user': current_user,
                'scenarios': scenarios,
                'title': "ISPU - Assignment task!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the assignment task page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the assignment task page.",
            'user': current_user,
            'menu': user_menu
        })


@router.post("/scenario/add_user/{user_id}", response_class=HTMLResponse)
async def post_task_assignment_for_curr_user(request: Request, user_id: int, tasks_ids: list[int] = Form(...),
                                             current_user: User = Depends(staff_user),
                                             session: AsyncSession = Depends(get_async_session)):
    try:
        for task_id in tasks_ids:
            admission = Admission(status=AdmissionStatus.ACTIVE, user_id=user_id, rating="0", scenario_id=task_id)
            session.add(admission)
        await session.commit()
        response = RedirectResponse(url=request.url_for("get_profile_for_id_page", user_id=user_id),
                                    status_code=HTTPStatus.MOVED_PERMANENTLY)
        return response
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the assignment task page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the assignment task page.",
            'user': current_user,
            'menu': user_menu
        })


# endregion


# region GetModelList

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
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the user page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the user page.",
            'user': user,
            'menu': user_menu
        })


@router.get("/tasks", response_class=HTMLResponse)
async def get_tasks_page(request: Request, user: User = Depends(current_user),
                         session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(Admission).where(user.id == Admission.user_id).order_by("status")
        result = await session.execute(query)
        admission = result.scalars().all()
        return templates.TemplateResponse(
            "/location/tasks.html",
            {
                "request": request,
                'user': user,
                "admissions": admission,
                'title': "ISPU - Tasks!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the task page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the task page.",
            'user': user,
            'menu': user_menu
        })


@router.get("/scenario", response_class=HTMLResponse)
async def get_scenario_page(request: Request, user: User = Depends(staff_user),
                            session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(Scenario).order_by(Scenario.id)
        result = await session.execute(query)
        scenarios = result.scalars().all()
        return templates.TemplateResponse(
            "/location/scenario.html",
            {
                'request': request,
                'user': user,
                "scenarios": scenarios,
                'title': "ISPU - Scenario",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There was some problem with the scripts.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There was some problem with the scripts.",
            'user': user,
            'menu': user_menu
        })


@router.get("/locations", response_class=HTMLResponse)
async def get_location_page(request: Request, user: User = Depends(staff_user),
                            session: AsyncSession = Depends(get_async_session)):
    try:
        locations = await get_location_list(session=session)
        return templates.TemplateResponse(
            "/location/location.html",
            {
                'request': request,
                'user': user,
                "locations": locations,
                'title': "ISPU - Scenario",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There was some problem with the scripts.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There was some problem with the scripts.",
            'user': user,
            'menu': user_menu
        })


@router.get("/models", response_class=HTMLResponse)
async def get_model_page(request: Request, user: User = Depends(staff_user),
                         session: AsyncSession = Depends(get_async_session)):
    try:
        models = await get_all_models(session=session)
        return templates.TemplateResponse(
            "/location/model.html",
            {
                'request': request,
                'user': user,
                "models": models,
                'title': "ISPU - Scenario",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There was some problem with the scripts.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There was some problem with the scripts.",
            'user': user,
            'menu': user_menu
        })


@router.get("/sensors", response_class=HTMLResponse)
async def get_sensor_page(request: Request, user: User = Depends(staff_user),
                          session: AsyncSession = Depends(get_async_session)):
    try:
        sensors = await get_all_sensors(session=session)
        return templates.TemplateResponse(
            "/location/sensors.html",
            {
                'request': request,
                'user': user,
                "sensors": sensors,
                'title': "ISPU - Scenario",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There was some problem with the scripts.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There was some problem with the scripts.",
            'user': user,
            'menu': user_menu
        })


# endregion


#  region Update Model
@router.get("/model/update/{model_id}", response_class=HTMLResponse)
async def get_update_model_page(request: Request, model_id: int, current_user: User = Depends(administrator_user),
                                session: AsyncSession = Depends(get_async_session)):
    try:
        model = await get_model_for_id(model_id=model_id, session=session)
        sensor_types = await get_all_sensor_types(session=session)

        return templates.TemplateResponse(
            "/staff/update/model/update_model.html",
            {
                "request": request,
                'user': current_user,
                "model": model,
                "sensor_types": sensor_types,
                'title': "ISPU - User Profile!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })


@router.post("/model/update/fields/{model_id}", response_class=HTMLResponse)
async def get_update_model_page_choice_field(request: Request, model_id: int,
                                             current_user: User = Depends(administrator_user),
                                             model_sensor_type: str = Form(...),
                                             session: AsyncSession = Depends(get_async_session)):
    try:
        model = await get_model_for_id(model_id=model_id, session=session)
        sensor_values = await get_sensor_value_for_name(sensor_name=model_sensor_type, session=session)
        selected_fields = model.specification
        return templates.TemplateResponse(
            "/staff/update/model/update_model_field.html",
            {
                "request": request,
                'user': current_user,
                "model": model,
                "sensor_values": sensor_values,
                "model_sensor_type": model_sensor_type,
                'selected_fields': selected_fields,
                'title': "ISPU - User Profile!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })


@router.post("/model/update/{model_id}", response_class=HTMLResponse)
async def post_update_model_page(request: Request, model_id: int, fields_selected: list[int] = Form(None),
                                 model_sensor_type: str = Form(...),
                                 current_user: User = Depends(administrator_user),
                                 session: AsyncSession = Depends(get_async_session)):
    try:
        if not fields_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали параметры для модели.",
                'user': current_user,
                'menu': user_menu
            })
        model = await get_model_for_id(model_id=model_id, session=session)
        fields = await get_sensor_values_for_id(session=session, fields_id=fields_selected)
        fields_dict = dict()
        for field in fields:
            fields_dict[field.field] = f"{field.value} {field.measurement}"
        id: int = await create_or_get_sensor_type(session=session, sensor_type_name=model_sensor_type)
        model.specification = fields_dict
        model.model_type = id
        session.add(model)
        await session.commit()
        return RedirectResponse(url=request.url_for("get_model_for_id_page", model_id=model.id),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })


# endregion


#  region Update Sensor
@router.get("/sensor/update/{sensor_id}", response_class=HTMLResponse)
async def get_update_sensor_page(request: Request, sensor_id: int, current_user: User = Depends(administrator_user),
                                 session: AsyncSession = Depends(get_async_session)):
    try:
        models = await get_all_models(session=session)
        sensor = await get_sensor_for_id(session=session, sensor_id=sensor_id)
        return templates.TemplateResponse(
            "/staff/update/sensor/update_sensor.html",
            {
                "request": request,
                'user': current_user,
                "models": models,
                "sensor": sensor,
                'title': "ISPU - User Profile!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the model page.",
            'user': current_user,
            'menu': user_menu
        })


@router.post("/sensor/update/{sensor_id}", response_class=HTMLResponse)
async def post_update_model_page(request: Request, sensor_id: int, model_selected: int = Form(None),
                                 name: str = Form(...),
                                 KKS: str = Form(...),
                                 current_user: User = Depends(administrator_user),
                                 session: AsyncSession = Depends(get_async_session)):
    try:
        if not model_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали модель для сенсора.",
                'user': current_user,
                'menu': user_menu
            })
        sensor = await get_sensor_for_id(session=session, sensor_id=sensor_id)
        sensor.KKS = KKS
        sensor.name = name
        sensor.model_id = model_selected
        session.add(sensor)
        await session.commit()
        return RedirectResponse(url=request.url_for("get_sensor_page"),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the sensor page.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the sensor page.",
            'user': current_user,
            'menu': user_menu
        })


# endregion


# region Update Location
@router.get("/location/update/{location_id}", response_class=HTMLResponse)
async def get_update_location_page(request: Request,
                                   location_id: int,
                                   user: User = Depends(administrator_user),
                                   session: AsyncSession = Depends(get_async_session)):
    try:
        location: Location = await get_location_for_id(session=session, location_id=location_id)
        sensors = await get_all_sensors(session=session)
        sensor_for_location = location.sensors
        return templates.TemplateResponse(
            "/staff/update/location/update_location.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'sensors_options': sensors,
                'location': location,
                'sensor_for_location': sensor_for_location,
                'status_options': LocationStatus,
                'title': "ISPU - Create scenario!",
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/location/create/{location_id}", response_class=HTMLResponse)
async def post_update_location_page(request: Request,
                                    location_id: int,
                                    sensor_selected: list[int] = Form(None),
                                    name: str = Form(...), prefab: str = Form(...),
                                    status: LocationStatus = Form(...),
                                    user: User = Depends(administrator_user),
                                    session: AsyncSession = Depends(get_async_session)):
    try:
        if not sensor_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали сенсор для локации.",
                'user': user,
                'menu': user_menu
            })
        location = await get_location_for_id(session=session, location_id=location_id)
        await delete_all_connection_location_model(session=session, location_id=location_id)
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
        return RedirectResponse(url=request.url_for("get_location_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


# endregion


# region Update Scenario


@router.get("/scenario/update/{scenario_id}", response_class=HTMLResponse)
async def get_update_scenario_page(request: Request, scenario_id: int,
                                   user: User = Depends(administrator_user),
                                   session: AsyncSession = Depends(get_async_session)):
    try:
        scenario = await get_scenario_for_id(session=session, scenario_id=scenario_id)
        locations = await get_location_list(session=session)
        return templates.TemplateResponse(
            "/staff/update/scenario/choice_location.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Update scenario!",
                'locations': locations,
                'scenario': scenario,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/scenario/update/model/{scenario_id}", response_class=HTMLResponse)
async def get_choice_sensor_for_update_scenario_page(request: Request, scenario_id: int,
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
        scenario = await get_scenario_for_id(session=session, scenario_id=scenario_id)
        location = await get_location_for_id(session=session, location_id=location_selected)
        is_changed = False
        if scenario.location.id == location.id:
            is_changed = True
        sensors = location.sensors
        return templates.TemplateResponse(
            "/staff/update/scenario/choice_sensor.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Update scenario!",
                'location_selected': location_selected,
                'scenario': scenario,
                'sensor_options': sensors,
                'is_changed': is_changed,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/scenario/update/accident/{scenario_id}", response_class=HTMLResponse)
async def get_choice_accident_for_update_scenario_page(request: Request,
                                                       scenario_id: int, location_selected: int = Form(...),
                                                       sensor_selected: int = Form(None),
                                                       user: User = Depends(administrator_user),
                                                       session: AsyncSession = Depends(get_async_session)):
    try:
        if not sensor_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали сенсор для сценария.",
                'user': user,
                'menu': user_menu
            })
        scenario = await get_scenario_for_id(session=session, scenario_id=scenario_id)
        sensor = await get_sensor_for_id(session=session, sensor_id=sensor_selected)
        is_changed = False
        if scenario.sensor.id == sensor.id:
            is_changed = True
        return templates.TemplateResponse(
            "/staff/update/scenario/choice_accident.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Update scenario!",
                'location_selected': location_selected,
                'sensor_selected': sensor_selected,
                'scenario': scenario,
                'accidents_options': sensor.model.accidents,
                'is_changed': is_changed,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/scenario/update/{scenario_id}/", response_class=HTMLResponse)
async def post_update_scenario(request: Request,
                               scenario_id: int,
                               location_selected: int = Form(...), sensor_selected: int = Form(...),
                               accident_selected: list[int] = Form(None),
                               name: str = Form(max_length=255),
                               user: User = Depends(administrator_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
        if not accident_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали аварии для сценария.",
                'user': user,
                'menu': user_menu
            })
        scenario = await get_scenario_for_id(scenario_id=scenario_id, session=session)
        await delete_all_connection_scenario_accident(session=session, scenario_id=scenario_id)
        scenario.name = name
        scenario.sensor_id = sensor_selected
        scenario.location_id = location_selected
        session.add(scenario)
        sensor_accident = [
            {"scenario_id": scenario.id, "accident_id": accident_id}
            for accident_id in accident_selected
        ]
        await session.execute(insert(scenario_accident_association).values(sensor_accident))
        await session.commit()
        return RedirectResponse(url=request.url_for("get_scenario_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create scenario page.",
            'user': user,
            'menu': user_menu
        })


# endregion


# region DeleteAccidentForScenario
@router.post("/accident/delete/scenario/{accident_id}/{scenario_id}")
async def delete_accident_for_scenario_page(accident_id: int, scenario_id: int,
                                            session: AsyncSession = Depends(get_async_session),
                                            user: User = Depends(administrator_user)):
    try:
        await delete_accident_for_scenario(session=session, scenario_id=scenario_id, accident_id=accident_id)
        return {"detail": "Accident deleted successfully"}
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        print(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


# endregion


# region DeleteAccidentForModel
@router.post("/accident/delete/model/{accident_id}/{model_id}")
async def delete_accident_for_model_page(accident_id: int, model_id: int,
                                         session: AsyncSession = Depends(get_async_session),
                                         user: User = Depends(administrator_user)):
    try:
        await delete_accident_for_model(session=session, model_id=model_id, accident_id=accident_id)
        return {"detail": "Accident deleted successfully"}
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        print(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


# endregion


# region AddAccidentForScenario


@router.get("/accident/scenario/add/{scenario_id}", response_class=HTMLResponse)
async def get_add_accident_for_scenario_page(
        request: Request,
        scenario_id: int,
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        scenario: Scenario = await get_scenario_for_id(scenario_id=scenario_id, session=session)
        scenario_accidents = scenario.accidents
        model_accidents = scenario.sensor.model.accidents
        return templates.TemplateResponse(
            "/staff/update/accident/add_accident_scenario.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Add accident!",
                'scenario_accidents': scenario_accidents,
                'model_accidents': model_accidents,
                'scenario': scenario,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })


@router.post("/accident/add/{scenario_id}", response_class=HTMLResponse)
async def post_add_accident_for_scenario_page(
        request: Request,
        scenario_id: int,
        accidents_selected: list[int] = Form(None),
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        await delete_all_connection_scenario_accident(session=session, scenario_id=scenario_id)
        await add_accidents_for_scenario(session=session, accidents_id=accidents_selected, scenario_id=scenario_id)
        return RedirectResponse(request.url_for("get_scenario_for_id_page", scenario_id=scenario_id),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)

    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the add accident page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the add accident page.",
            'user': user,
            'menu': user_menu
        })


# endregion


# region AddAccidentForModel
@router.get("/accident/model/add/{model_id}", response_class=HTMLResponse)
async def get_add_accident_model_page(
        request: Request,
        model_id: int,
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        model = await get_model_for_id(session=session, model_id=model_id)
        return templates.TemplateResponse(
            "/staff/update/accident/add_accident_model.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Add accident!",
                'model': model,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with the create model page.",
            'user': user,
            'menu': user_menu
        })


# endregion

# region StartApp


@router.get("/scenario/start/{admission_id}", response_class=HTMLResponse)
async def start_admission_app(
        request: Request,
        admission_id: int,
        user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        admission = await get_admission_for_id(admission_id=admission_id, session=session)
        path_parent = request.headers.get("REFERER")
        create_json_scenario(admission_json=admission.json_dump())
        start_app()
        response = RedirectResponse(url=path_parent, status_code=302)
        return response
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with start app.",
            'user': user,
            'menu': user_menu
        })
    except IOError as e:
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": str(e),
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with start app.",
            'user': user,
            'menu': user_menu
        })
# endregion
