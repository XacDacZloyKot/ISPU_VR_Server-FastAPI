from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin, exceptions, models, schemas
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.models import User
from src.auth.utils import get_user_db
from src.config import SECRET_KEY

SECRET = SECRET_KEY


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def create(
            self,
            user_create: schemas.UC,
            safe: bool = False,
            request: Optional[Request] = None,
    ) -> models.UP:
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise exceptions.UserAlreadyExists()

        user_dict = (
            user_create.create_update_dict()
            if safe
            else user_create.create_update_dict_superuser()
        )
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)
        user_dict["role_id"] = 1
        user_dict["is_staff"] = False

        created_user = await self.user_db.create(user_dict)

        await self.on_after_register(created_user, request)

        return created_user

    async def authenticate(
        self, credentials: OAuth2PasswordRequestForm
    ) -> Optional[models.UP]:
        try:
            user = await self.get_by_email(credentials.username)
        except exceptions.UserNotExists:
            self.password_helper.hash(credentials.password)
            return None

        verified, updated_password_hash = self.password_helper.verify_and_update(
            credentials.password, user.hashed_password
        )
        if not verified:
            return None
        if updated_password_hash is not None:
            await self.user_db.update(user, {"hashed_password": updated_password_hash})
        return user


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
