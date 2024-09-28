from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from fastapi import Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import get_jwt_strategy, current_user
from src.auth.models import User, Admission
from src.database import get_async_session
from src.admission.crud import (
    get_admissions_by_user,
    get_last_admission_task, get_admissions
)
from src.pages.router import templates
from src.pages.utils import (authenticate,
                             authenticate_for_username,
                             user_menu,
                             create,
                             logout as logout_func, )
from src.auth.base_config import staff_user
from src.users.crud import get_user_for_id, get_users

router = APIRouter(
    prefix='/pages/users213123123',
    tags=['Users']
)


@router.get("/index", response_class=HTMLResponse)
async def get_index_page(request: Request, user=Depends(current_user)):
    return templates.TemplateResponse("/profile/index.html", {
        'request': request,
        'user': user,
        'menu': user_menu,
        'title': "ISPU - Главная страница!"
    })


@router.get("/login/admin", response_class=HTMLResponse)
async def get_login_admin(request: Request):
    return templates.TemplateResponse("/auth/loginAdmin.html", {'request': request})


@router.post("/login/admin", response_class=RedirectResponse)
async def post_login_admin(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        user = await authenticate(email=email, password=password)
        if not user or (user.is_superuser == False and user.is_staff == False):
            return templates.TemplateResponse("/auth/loginAdmin.html", {
                'request': request,
                'error': "У вас недостаточно прав или такого пользователя не существует."
            })

        token = await get_jwt_strategy().write_token(user)
        response = RedirectResponse(url=request.url_for("get_index_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
        response.set_cookie(key="user-cookie", value=token, httponly=True, path="/")
        return response

    except HTTPException as e:
        print(e.detail)
        return templates.TemplateResponse("/auth/loginAdmin.html", {
            'request': request,
            'error': "Ошибка при авторизации!"
        })

    except Exception as e:
        print(e)
        return templates.TemplateResponse("/auth/loginAdmin.html", {
            'request': request,
            'error': "Ошибка при авторизации!"
        })


@router.get("/logout")
async def logout(request: Request, user=Depends(current_user)):
    try:
        redirect_response = RedirectResponse(url=request.url_for("get_login_user"), status_code=302)
        response_cookie = await logout_func(request=request, user=user, response=redirect_response)
        return response_cookie

    except Exception as e:
        print(e)
        return templates.TemplateResponse("/auth/loginUser.html", {
            'request': request,
            'error': "Ошибка при попытке выхода."
        })


@router.get("/login/user", response_class=HTMLResponse)
async def get_login_user(request: Request):
    return templates.TemplateResponse("/auth/loginUser.html", {'request': request})


@router.post("/login/user", response_class=RedirectResponse)
async def post_login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        user = await authenticate_for_username(username=username, password=password)
        if not user:
            return templates.TemplateResponse("/auth/loginUser.html", {
                'request': request,
                'error': "Такого пользователя не существует."
            })

        token = await get_jwt_strategy().write_token(user)
        if user.is_superuser or user.is_staff:
            response = RedirectResponse(url=request.url_for("get_index_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
        else:
            response = RedirectResponse(url=request.url_for("get_home_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
        response.set_cookie(key="user-cookie", value=token, httponly=True, path="/")
        return response

    except Exception as e:
        print(e)
        return templates.TemplateResponse("/auth/loginUser.html", {
            'request': request,
            'error': "Такого пользователя не существует."
        })


@router.get("/registration", response_class=HTMLResponse)
async def get_registration(request: Request):
    return templates.TemplateResponse("/auth/registration.html", {'request': request})


@router.post("/registration", response_class=RedirectResponse)
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
            return templates.TemplateResponse("/auth/registration.html", {
                'request': request,
                'error': "Неверно введены данные!"
            })
        response = RedirectResponse(url=request.url_for("get_login_user"), status_code=HTTPStatus.MOVED_PERMANENTLY)
        return response
    except HTTPException as e:
        print(f"HTTPException ошибка при создании пользователя: {e.detail}")
        return templates.TemplateResponse("/auth/registration.html", {
            'request': request,
            'error': "Неверно введены данные!"
        })
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при создании пользователя: {e}")
        return templates.TemplateResponse("/auth/loginUser.html", {
            'request': request, 'error': "Неверно введены данные!"})
    except Exception as e:
        print(e)
        return templates.TemplateResponse("/auth/loginAdmin.html", {
            'request': request, 'error': "Возникла проблема при создании пользователя."})


@router.get("/home", response_class=HTMLResponse)
async def get_home_page(request: Request, user: User = Depends(current_user),
                        session: AsyncSession = Depends(get_async_session)):
    try:
        admission = await get_admissions_by_user(user_id=user.id, session=session)
        sum_rating = await Admission.get_average_rating_for_user(user_id=user.id, session=session)
        last_admission = get_last_admission_task(list_admission_tasks=admission)
        return templates.TemplateResponse(
            "/profile/home.html",
            {
                'request': request,
                'user': user,
                'admissions': admission,
                'last_admission': last_admission,
                'title': "ISPU - Главная страница!",
                'menu': user_menu,
                'sum_rating': sum_rating,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при переходе на главную страницу: {e}")
        return templates.TemplateResponse('profile/index.html', {
            'request': request, 
            'error': "Ошибка при переходе на главную страницу.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse('profile/index.html', {
            'request': request, 
            'error': "Ошибка при переходе на главную страницу.",
            'user': user,
            'menu': user_menu
        })


@router.get("/id/{user_id}", response_class=HTMLResponse)
async def get_profile_for_id(request: Request, user_id: int, user: User = Depends(staff_user),
                             session: AsyncSession = Depends(get_async_session)):
    try:
        curr_user = await get_user_for_id(user_id, session)
        admission = await get_admissions_by_user(user_id, session)
        sum_rating = await Admission.get_average_rating_for_user(user_id=user_id, session=session)
        return templates.TemplateResponse(
            "/profile/profile_user_for_admin.html",
            {
                'request': request,
                'user': user,
                "user_for_id": curr_user,
                "sum_rating": sum_rating,
                "admissions": admission,
                'title': "ISPU - User Profile!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при переходе в профиль пользователя: {e}")
        return templates.TemplateResponse("profile/index.html", {
            'request': request,
            'error': "Ошибка при переходе в профиль пользователя",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при переходе в профиль пользователя: {e}")
        return templates.TemplateResponse("profile/index.html", {
            'request': request,
            'error': "Ошибка при переходе в профиль пользователя.",
            'user': user,
            'menu': user_menu
        })



@router.get("/update/{user_id}", response_class=HTMLResponse)
async def get_update_user(request: Request, user_id: int, user: User = Depends(staff_user),
                          session: AsyncSession = Depends(get_async_session)):
    try:
        curr_user = await get_user_for_id(user_id=user_id, session=session)
        return templates.TemplateResponse(
            "/staff/update/user/update_user.html",
            {
                'request': request,
                'user': user,
                'current_user': curr_user,
                'menu': user_menu,
                'title': "ISPU - Обновление пользователя",
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при открытии страницы обновления параметров пользователя: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка с БД при открытии страницы параметров пользователя.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при открытии страницы обновления параметров пользователя: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка с БД при открытии страницы параметров пользователя.",
            'user': user,
            'menu': user_menu
        })


@router.post("/update/{user_id}/", response_class=HTMLResponse)
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
        print(f"SQLAlchemy ошибка при открытии страницы обновления параметров пользователя: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка с БД при обновлении параметров пользователя.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при открытии страницы обновления параметров пользователя: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при обновлении параметров пользователя.",
            'user': user,
            'menu': user_menu
        })


@router.get("/", response_class=HTMLResponse)
async def get_users_page(request: Request, user: User = Depends(staff_user),
                         session: AsyncSession = Depends(get_async_session)):
    try:
        users = await get_users(session=session)
        return templates.TemplateResponse(
            "/staff/user.html",
            {
                "request": request,
                'user': user,
                "users": users,
                'title': "ISPU - Пользователи",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при открытии страницы пользователей: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при открытии страницы пользователей.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при открытии страницы пользователей: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при открытии страницы пользователей.",
            'user': user,
            'menu': user_menu
        })


@router.get("/tasks", response_class=HTMLResponse)
async def get_tasks(request: Request, user: User = Depends(current_user),
                    session: AsyncSession = Depends(get_async_session)):
    try:
        admission = await get_admissions(session=session, user_id=user.id)
        return templates.TemplateResponse(
            "/location/tasks.html",
            {
                "request": request,
                'user': user,
                "admissions": admission,
                'title': "ISPU - Задачи!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при открытии страницы задач: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при получении задач.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при открытии страницы задач: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при получении задач.",
            'user': user,
            'menu': user_menu
        })