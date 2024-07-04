from typing import Optional

from fastapi._compat import PYDANTIC_VERSION
from fastapi_users import schemas
from pydantic import ConfigDict

PYDANTIC_V2 = PYDANTIC_VERSION.startswith("2.")


class UserRead(schemas.BaseUser[int]):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    role_id: int
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    if PYDANTIC_V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class UserCreate(schemas.BaseUserCreate):
    last_name: str
    first_name: str
    username: str
    role_id: int
    is_staff: bool
    email: str
    password: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False


class UserUpdate(schemas.BaseUserUpdate):
    pass
