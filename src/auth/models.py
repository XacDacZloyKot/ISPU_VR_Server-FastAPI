import json
from datetime import datetime
from enum import Enum

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Integer, String, Boolean, ForeignKey, Column, TIMESTAMP, Enum as SQLAEnum, Table, select, func, \
    Float, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from slugify import slugify

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

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=True, doc="Почта")
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
    user = relationship("User", back_populates="admissions", foreign_keys="Admission.user_id",
                                        lazy="selectin")
    scenario = relationship("Scenario", back_populates="admissions",
                                                foreign_keys="Admission.scenario_id", lazy="selectin")
    is_ready = mapped_column(DateTime, nullable=True, default=None, doc="Время, когда поставили оценку")

    @classmethod
    async def get_average_rating_for_user(cls, user_id: int, session: AsyncSession) -> float:
        result = await session.execute(
            select(func.avg(cls.rating).cast(Float)).where(user_id == cls.user_id)
        )
        average_rating = result.scalar()
        return average_rating or 0.0

    @staticmethod
    def set_rating(instance, value):
        instance.rating = value
        if value is not None and value != "0":
            instance.is_ready = datetime.utcnow()
            instance.status = "COMPLETED"
        else:
            instance.is_ready = None

    def json_dump(self) -> str:
        json_object = {
            'response': {
                'id': self.id,
                'status': 200,
                'scenario': {
                    'id': self.scenario.id,
                    'name': self.scenario.name,
                    'sensor': {
                        'id': self.scenario.sensor.id,
                        'name': self.scenario.sensor.name,
                        'KKS': self.scenario.sensor.KKS,
                        'model': {
                            'id': self.scenario.sensor.model.id,
                            'name': self.scenario.sensor.model.model_type.name,
                            'specification': {
                                slugify(key, separator="_"): value
                                for key, value in self.scenario.sensor.model.specification.items()
                            },
                        }
                    },
                    'accidents': [
                        {
                            'name': accident.name,
                            'mechanical_accident': accident.mechanical_accident,
                            'change_value': accident.change_value,
                        }
                        for accident in self.scenario.accidents
                    ]
                }
            }
        }
        return json.dumps(json_object, ensure_ascii=False)

    def __str__(self):
        return f"ID: {self.id} | name: {self.scenario.name} | Rating: {self.rating}"


class Scenario(Base):
    __tablename__ = "scenario"

    name = Column(String(255), nullable=False, doc="Название сценария")
    # Связь с Sensor
    sensor_id: Mapped[int] = mapped_column(ForeignKey("sensor.id"), nullable=False)
    sensor = relationship("Sensor",
                          back_populates="scenarios",
                          foreign_keys='Scenario.sensor_id',
                          lazy='selectin')

    # Связь с Location
    location_id: Mapped[int] = mapped_column(ForeignKey("location.id"), nullable=False)
    location = relationship("Location", back_populates="scenarios",
                            foreign_keys='Scenario.location_id', lazy='selectin')

    # Обратная совместимость
    admissions = relationship("Admission", back_populates="scenario", lazy="selectin")
    accidents = relationship("Accident",
                             secondary=scenario_accident_association,
                             back_populates="scenarios",
                             lazy="selectin")