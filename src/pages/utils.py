import contextlib

from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.base_config import auth_backend, get_jwt_strategy
from src.auth.manager import get_user_manager
from src.auth.utils import get_user_db
from src.database import get_async_session

get_async_session_con = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


user_menu = [
    {
        "name": "СТАТИСТИКА",
        "urls": [
            ("Домашняя страница", "#"),
        ]
    },
    {
        "name": "ТРЕНАЖЕР",
        "urls": [
            ("Локации", "get_location"),
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
        print(e)


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
        print(e)
