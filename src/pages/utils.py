import contextlib
import os
import subprocess

from fastapi import HTTPException, Request
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

from datetime import datetime

from sqlalchemy import Sequence
import json
import psutil

from src.auth.models import Admission, User, Scenario
from src.auth.base_config import auth_backend, get_jwt_strategy
from src.auth.manager import get_user_manager
from src.auth.utils import get_user_db
from src.database import get_async_session
from src.auth.schemas import UserCreate

get_async_session_con = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


user_menu = [
    {
        "name": "СТАТИСТИКА",
        "access": "user",
        "urls": [
            ("Домашняя страница", "get_home_page"),
            ("Активные задачи", "get_tasks"),
        ]
    },
    {
        "name": "ТРЕНАЖЕР",
        "access": "staff",
        "urls": [
            ("Модели КИП", "get_model_page"),
            ("Приборы КИП", "get_sensor_page"),
            ("Локации", "get_location_page"),
            ("Сценарии", "get_scenario"),
        ]
    },
    {
        "name": "АДМИНИСТРАТОР",
        "access": "staff",
        "urls": [
            ("Пользователи", "get_users_page"),
        ]
    },
    {
        "name": "СУПЕР АДМИН",
        "access": "admin",
        "urls": [
            ("Создание модели КИП", "get_create_model"),
            ("Создание прибора КИП", "get_create_sensor"),
            ("Создание локации", "get_create_location"),
            ("Создание сценария", "get_create_scenario"),
            ("Добавление параметров в базу данных прибора", "get_create_model_value"),
            ("Просмотр параметров базы данных прибора", "get_model_value"),
        ]
    },
]


async def authenticate(email: str, password: str):
    try:
        async with get_async_session_con() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.authenticate(
                        credentials=OAuth2PasswordRequestForm(username=email, password=password)
                    )
                    response: Response = await auth_backend.login(strategy=get_jwt_strategy(), user=user)
                    print(f"User auth {user.username} | Response {response.status_code}")
                    return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def authenticate_for_username(username: str, password: str):
    try:
        async with get_async_session_con() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.authenticate_for_username(
                        credentials=OAuth2PasswordRequestForm(username=username, password=password), session=session
                    )
                    response: Response = await auth_backend.login(strategy=get_jwt_strategy(), user=user)
                    print(f"User auth {user.username} | Response {response.status_code}")
                    return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def logout(request: Request, user: User, response: Response):
    strategy = auth_backend.get_strategy()
    token = request.cookies.get("user-cookie", None)
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    try:
        await auth_backend.logout(strategy=strategy, user=user, token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    response.delete_cookie(key="user-cookie", httponly=True, path="/")
    return response


async def create(username: str, password: str, first_name: str, last_name: str, patronymic: str, division: str):
    try:
        async with get_async_session_con() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    new_user = UserCreate(password=password,
                                          first_name=first_name,
                                          last_name=last_name,
                                          patronymic=patronymic,
                                          division=division,
                                          username=username)
                    user = await user_manager.create(new_user)
                    return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def get_last_admission_task(list_admission_tasks: Sequence[Admission]) -> Admission | None:
    if not list_admission_tasks:
        return None
    filtered_admissions = [admission for admission in list_admission_tasks if admission.is_ready is not None]
    if not filtered_admissions:
        return None
    last_admission = max(filtered_admissions, key=lambda admission: admission.is_ready)
    return last_admission


def create_json_scenario(admission_json, path="C:\\Users\\treen\\Desktop\\text.json"):
    with open(path, "w", encoding="utf-8") as file:
        file.write(admission_json)

def kill_existing_process(process_name):
    for proc in psutil.process_iter():
        try:
            if proc.name() == process_name:
                proc.kill()
                print(f"Процесс {process_name} завершен.")
        except psutil.ZombieProcess:
            pass
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            pass


def start_app(path="C:\\Users\\treen\\Desktop\\build\\Myproject.exe"):
    process_name = path.split('\\')[-1]
    print(process_name)
    try:
        if os.path.exists(path):
            kill_existing_process(process_name)

            print("Начал запуск приложения Unity")
            subprocess.Popen(path, shell=True)
            print("Запуск завершен")
        else:
            raise IOError("Проект не найден")
    except Exception as e:
        raise Exception(str(e))
