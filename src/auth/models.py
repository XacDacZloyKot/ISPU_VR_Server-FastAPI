from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import MetaData, Integer, String, Boolean, ForeignKey, Table, Column, JSON, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base

metadata = MetaData()


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False, doc="Почта")
    username = Column(String(255), nullable=False, unique=True, doc="Пользовательское имя")
    registered_at = Column(TIMESTAMP, default=datetime.utcnow)
    first_name = Column(String(255), doc="Имя")
    last_name = Column(String(255), doc="Фамилия")
    patronymic: Mapped[str] = mapped_column(
        String(50), nullable=True, doc="Отчество"
    )
    is_staff = Column(Boolean, default=False, doc="Сотрудник")
    hashed_password: Mapped[str] = mapped_column(
        String(length=1024), nullable=False, doc="Пароль"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Активный пользователь")
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, doc="Супер пользователь"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, doc="Верификация"
    )
    division: Mapped[bool] = mapped_column(String(50), doc="Подразделение")