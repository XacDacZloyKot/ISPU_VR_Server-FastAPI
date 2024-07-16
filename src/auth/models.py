from datetime import datetime
from enum import Enum

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Integer, String, Boolean, ForeignKey, Column, TIMESTAMP, Enum as SQLAEnum, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


# Промежуточная таблица для связи Many-to-Many между Scenario и Accident
scenario_accident_association = Table(
    'scenario_accident_association',
    Base.metadata,
    Column('scenario_id', Integer, ForeignKey('scenario.id')),
    Column('accident_id', Integer, ForeignKey('accident.id')),
    extend_existing=True
)


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "user"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False, doc="Почта")
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, doc="Пользовательское имя")
    registered_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    first_name: Mapped[str] = mapped_column(String(255), doc="Имя")
    last_name: Mapped[str] = mapped_column(String(255), doc="Фамилия")
    patronymic: Mapped[str] = mapped_column(String(50), nullable=True, doc="Отчество")
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, doc="Сотрудник")
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False, doc="Пароль")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Активный пользователь")
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, doc="Супер пользователь")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, doc="Верификация")
    division: Mapped[str] = mapped_column(String(50), doc="Подразделение")
    #  Обратная совместимость
    admissions: Mapped["Admission"] = relationship("Admission", back_populates="user", lazy="selectin")


class AdmissionStatus(Enum):
    INACTIVE = "Не активно"
    ACTIVE = "Активно"
    COMPLETED = "Завершено"
    EXAMINATION = "Проверяется"


class Admission(Base):
    __tablename__ = "admission"

    rating: Mapped[str] = mapped_column(String(4), nullable=True, default="0", doc="Рейтинг")
    status: Mapped[AdmissionStatus] = mapped_column(SQLAEnum(AdmissionStatus), default=AdmissionStatus.INACTIVE,
                                                    nullable=False, doc="Статус заявки")
    #  Создание связи ForeignKey
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenario.id"), nullable=False)
    # Связь объектов(ForeignKey)
    user: Mapped["User"] = relationship("User", back_populates="admissions", foreign_keys="Admission.user_id",
                                        lazy="selectin")
    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="admissions",
                                                foreign_keys="Admission.scenario_id", lazy="selectin")


class Scenario(Base):
    __tablename__ = "scenario"

    #  Создание связи ForeignKey
    location_id: Mapped[int] = mapped_column(ForeignKey("location.id"), nullable=False)
    model_id: Mapped[int] = mapped_column(ForeignKey("model.id"), nullable=False)
    # Связь объектов(ForeignKey)
    location: Mapped["Location"] = relationship("Location", back_populates="scenarios",
                                                foreign_keys="Scenario.location_id", lazy="selectin")
    model: Mapped["Model"] = relationship("Model", back_populates="scenarios", foreign_keys="Scenario.model_id",
                                          lazy="selectin")
    #  Обратная совместимость
    admissions: Mapped[Admission] = relationship("Admission", back_populates="scenario", lazy="selectin")
    accidents = relationship("Accident", secondary=scenario_accident_association, back_populates="scenarios",
                             lazy="selectin")
