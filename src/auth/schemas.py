from typing import Optional

from fastapi._compat import PYDANTIC_VERSION
from fastapi_users import schemas
from pydantic import ConfigDict

PYDANTIC_V2 = PYDANTIC_VERSION.startswith("2.")


class UserRead(schemas.BaseUser[int]):
    email: str
    username: str
    first_name: str
    last_name: str
    patronymic: str
    is_staff: Optional[bool] = False
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
    division: str

    if PYDANTIC_V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class UserCreate(schemas.BaseUserCreate):
    email: str
    username: str
    first_name: str
    last_name: str
    patronymic: str
    is_staff: Optional[bool] = False
    password: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
    division: str


class UserUpdate(schemas.BaseUserUpdate):
    pass
