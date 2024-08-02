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

from src.auth.base_config import get_jwt_strategy, current_user, staff_user
from src.auth.models import User, Admission, AdmissionStatus, Scenario
from src.database import get_async_session
from src.pages.crud import (
    get_admission_for_user_id,
    get_user_for_id,
    get_scenario_for_id,
    get_users_without_scenario,
    get_admission_for_id, get_name_sensor_value, get_sensor_value_for_name, get_sensor_values_for_id,
    create_or_get_sensor_type, get_all_models, get_location_list, get_location_for_id,
    get_sensor_for_id, get_model_for_id,
)
from src.pages.utils import (authenticate,
                             authenticate_for_username,
                             user_menu,
                             create,
                             get_last_admission_task,
                             logout as logout_func,
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


@router.get("/loginAdmin", response_class=HTMLResponse)
async def get_login_admin(request: Request):
    return templates.TemplateResponse("/auth/loginAdmin.html", {"request": request})


@router.post("/loginAdmin", response_class=HTMLResponse)
async def post_login_admin(request: Request, email: str = Form(...), password: str = Form(...)):
    user = await authenticate(email=email, password=password)
    if not user:
        return templates.TemplateResponse("/auth/loginAdmin.html", {"request": request, "error": "Failed to login"})

    token = await get_jwt_strategy().write_token(user)
    response = RedirectResponse(url="/pages/home/", status_code=302)
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


@router.get("/scenario", response_class=HTMLResponse)
async def get_scenario_page(request: Request, user: User = Depends(current_user),
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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request, "error": "There is some problem "
                                                                                                "with the home page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request, "error": "There is some problem "
                                                                                                "with the home page."})


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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request, "error": "There is some problem "
                                                                                                "with the user page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request, "error": "There is some problem "
                                                                                                "with the user page."})


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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request, "error": "There is some problem "
                                                                                                "with the task page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request, "error": "There is some problem "
                                                                                                "with the task page."})


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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the profile page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the profile page."})


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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request, "error": "There was some problem"
                                                                                                " with the scripts."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request, "error": "There was some problem"
                                                                                                " with the scripts."})


@router.get("/scenario/add/{scenario_id}", response_class=HTMLResponse)
async def get_task_assignment(request: Request, scenario_id: int, current_user: User = Depends(staff_user),
                              session: AsyncSession = Depends(get_async_session)):
    try:
        scenario = await get_scenario_for_id(scenario_id=scenario_id, session=session)
        users = await get_users_without_scenario(scenario_id=scenario_id, session=session)
        return templates.TemplateResponse(
            "/staff/add_task_user.html",
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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the assignment task page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the assignment task page."})


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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the assignment task page."})
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the assignment task page."})


@router.get("/scenario/create", response_class=HTMLResponse)
async def get_create_scenario_page(request: Request, user: User = Depends(staff_user),
                                   session: AsyncSession = Depends(get_async_session)):
    try:
        location = await get_location_list(session=session)
        return templates.TemplateResponse(
            "/staff/create_scenario/choice_location.html",
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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create scenario page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create scenario page."})


@router.post("/scenario/create/model/", response_class=HTMLResponse)
async def get_choice_model_for_scenario_page(request: Request, location_selected: int = Form(...),
                                             user: User = Depends(staff_user),
                                             session: AsyncSession = Depends(get_async_session)):
    try:
        location = await get_location_for_id(session=session, location_id=location_selected)
        sensors = location.sensors
        return templates.TemplateResponse(
            "/staff/create_scenario/choice_model.html",
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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create scenario page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create scenario page."})


@router.post("/scenario/create/accident/{location_selected}", response_class=HTMLResponse)
async def get_choice_accident_for_scenario_page(request: Request, location_selected: int,
                                                sensor_selected: int = Form(...), user: User = Depends(staff_user),
                                                session: AsyncSession = Depends(get_async_session)):
    try:
        sensor = await get_sensor_for_id(session=session, sensor_id=sensor_selected)
        print(sensor.model.accidents)
        return templates.TemplateResponse(
            "/staff/create_scenario/choice_accident.html",
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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create scenario page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create scenario page."})


@router.post("/scenario/create/{location_id}/{sensor_id}", response_class=HTMLResponse)
async def post_create_scenario(request: Request, location_id: int, sensor_id: int,
                               accident_selected: list[int] = Form(...), name: str = Form(max_length=255),
                               user: User = Depends(staff_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the assignment task page."})
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the assignment task page."})


@router.get("/users/update/{user_id}", response_class=HTMLResponse)
async def get_update_user_page(request: Request, user_id: int, user: User = Depends(staff_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
        current_user = await get_user_for_id(user_id=user_id, session=session)
        return templates.TemplateResponse(
            "/staff/update_user.html",
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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the update user page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the update user page."})


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
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the update user page."
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the update user page."
        })


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
            "/staff/update_admission_for_user.html",
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
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the update admission page."
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the update admission page."
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
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the update admission page."
        })
    except ValidationError as e:
        error_message = str(e)
        return templates.TemplateResponse("/staff/update_admission_for_user.html", {
            "request": request,
            "error": error_message,
            'admission': admission,
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the update admission page."
        })


@router.delete("/admission/delete/{admission_id}", name="delete_admission")
async def delete_admission(admission_id: int, session: AsyncSession = Depends(get_async_session), user: User = Depends(staff_user)):
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


@router.get("/model/create", response_class=HTMLResponse)
async def get_create_model_page(request: Request, user: User = Depends(staff_user),
                                session: AsyncSession = Depends(get_async_session)):
    try:
        sensor_value_names = await get_name_sensor_value(session=session)
        return templates.TemplateResponse(
            "/staff/create_model/choice_sensor_type.html",
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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create model page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create model page."})


@router.post("/model/create/fields/", response_class=HTMLResponse)
async def get_choice_fields(request: Request, model_selected: str = Form(...), user: User = Depends(staff_user),
                            session: AsyncSession = Depends(get_async_session)):
    try:
        print("Страница выбора полей")
        values = await get_sensor_value_for_name(session=session, sensor_name=model_selected)
        return templates.TemplateResponse(
            "/staff/create_model/choice_fields.html",
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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create model page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create model page."})


@router.post("/model/create/{models_name}", response_class=HTMLResponse)
async def create_model(
        request: Request,
        models_name: str,
        fields_selected: list[int] = Form(...),
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        fields = await get_sensor_values_for_id(session=session, fields_id=fields_selected)
        fields_dict = dict()
        for field in fields:
            fields_dict[field.field] = f"{field.value} {field.measurement}"
        id: int = await create_or_get_sensor_type(session=session, sensor_type_name=models_name)
        new_model = Model(specification=fields_dict, sensor_type_id=id)
        session.add(new_model)
        await session.commit()
        return RedirectResponse(url=request.url_for("get_add_accident_page", model_id=new_model.id),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the create model page."
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the create model page."
        })


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
            "/staff/create_model/add_accident.html",
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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create model page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the create model page."})


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
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the create model page."
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the create model page."
        })


@router.get("/location/create/", response_class=HTMLResponse)
async def get_create_location_page(request: Request,
                                   user: User = Depends(staff_user),
                                   session: AsyncSession = Depends(get_async_session)):
    try:
        models = await get_all_models(session=session)
        return templates.TemplateResponse(
            "/staff/create_location/create_location.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'models_options': models,
                'status_options': LocationStatus,
                'title': "ISPU - Create scenario!",
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the create scenario page."
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the create scenario page."})


@router.post("/location/create/", response_class=HTMLResponse)
async def post_create_location_page(request: Request,
                                    model_selected: list[int] = Form(...),
                                    name: str = Form(...), prefab: str = Form(...),
                                    status: LocationStatus = Form(...),
                                    user: User = Depends(staff_user),
                                    session: AsyncSession = Depends(get_async_session)):
    try:
        new_location = Location(name=name, status=status, prefab=prefab)
        session.add(new_location)
        await session.flush()
        location_model = [
            {"location_id": new_location.id, "model_id": model_id}
            for model_id in model_selected
        ]
        await session.execute(insert(sensor_location_association).values(location_model))
        await session.commit()
        return RedirectResponse(url=request.url_for("get_home_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        await session.rollback()
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the create scenario page."
        })
    except Exception as e:
        print(e)
        await session.rollback()
        return templates.TemplateResponse("auth/loginAdmin.html", {
            "request": request,
            "error": "There is some problem with the create scenario page."})
