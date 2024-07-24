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
from src.auth.models import User, Admission, AdmissionStatus, Scenario
from src.database import get_async_session
from src.pages.utils import authenticate, authenticate_for_username, user_menu, create
from src.sensor.models import Model, Location
from src.pages.crud import get_admission_for_id, get_user_for_id, get_scenario_for_id, get_users_without_scenario

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
    response = RedirectResponse(url="/pages/home/", status_code=302)
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
        return templates.TemplateResponse("/auth/registration.html", {"request": request,
                                                                      "error": "Неверно введены данные!"})
    response = RedirectResponse(url="/pages/loginUser/", status_code=302)
    return response


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
        admission = await get_admission_for_id(user_id=user.id, session=session)
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
        admission = await get_admission_for_id(user_id, session)
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


@router.get("/add-scenario/{scenario_id}", response_class=HTMLResponse)
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


@router.post("/add-scenario/{scenario_id}", response_class=HTMLResponse)
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
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the assignment task page."})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("auth/loginAdmin.html", {"request": request,
                                                                   "error": "There is some problem "
                                                                            "with the assignment task page."})





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
