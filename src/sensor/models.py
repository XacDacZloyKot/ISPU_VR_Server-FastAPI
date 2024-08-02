from enum import Enum

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, JSON, Enum as SQLAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.database import Base

# Промежуточная таблица для связи Many-to-Many между Scenario и Accident
scenario_accident_association = Table(
    'scenario_accident_association',
    Base.metadata,
    Column('scenario_id', Integer, ForeignKey('scenario.id')),
    Column('accident_id', Integer, ForeignKey('accident.id')),
    extend_existing=True
)


# Определим промежуточную таблицу для связи many-to-many между Model и Accident
model_accident_association = Table(
    'model_accident_association',
    Base.metadata,
    Column('model_id', Integer, ForeignKey('model.id')),
    Column('accident_id', Integer, ForeignKey('accident.id')),
    extend_existing = True
)

# Промежуточная таблица для связи Many-to-Many между Sensor и Location
sensor_location_association = Table(
    'sensor_location_association',
    Base.metadata,
    Column('sensor_id', Integer, ForeignKey('sensor.id')),
    Column('location_id', Integer, ForeignKey('location.id')),
    extend_existing=True
)


class Model(Base):
    __tablename__ = "model"

    specification: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Связь с Sensor (один ко многим)
    sensors = relationship("Sensor", back_populates="model")

    # Связь с SensorType
    sensor_type_id: Mapped[int] = mapped_column(ForeignKey('sensortype.id'))
    sensor_type = relationship("SensorType",
                               back_populates="models",
                               foreign_keys='Model.sensor_type_id',
                               lazy='selectin')

    # Связь many-to-many через промежуточную таблицу
    accidents = relationship("Accident",
                             secondary=model_accident_association,
                             back_populates="models",
                             lazy="subquery")

    def __str__(self):
        return f"ID: {self.id} | Имя: {self.sensor_type.name}"


class SensorType(Base):
    __tablename__ = "sensortype"

    name = Column(String(255), doc="Тип датчика")
    #  Обратная совместимость
    models = relationship("Model", back_populates="sensor_type", lazy="selectin")


class Accident(Base):
    __tablename__ = "accident"

    name = Column(String(255), doc="Ошибка")
    mechanical_accident = Column(Boolean, doc="Механическое повреждение")
    change_value = Column(JSON, doc="Изменяемое значение")

    # Связь many-to-many(промежуточная таблица)
    models = relationship("Model", secondary=model_accident_association, back_populates="accidents",
                          lazy="subquery")

    scenarios = relationship("Scenario", secondary=scenario_accident_association, back_populates="accidents",
                             lazy="subquery")


class LocationStatus(Enum):
    DEVELOPING = "В разработке"
    INACTIVE = "Не доступна"
    COMPLETED = "Готова"


class Location(Base):
    __tablename__ = "location"

    status: Mapped[LocationStatus] = mapped_column(SQLAEnum(LocationStatus), default=LocationStatus.INACTIVE,
                                                    nullable=False, doc="Статус локации")
    name: Mapped[str] = mapped_column(String(255), doc="Название локации")
    prefab: Mapped[str] = mapped_column(String(300), doc="Путь до префаба")

    # Связь many-to-many через промежуточную таблицу с Sensor
    sensors = relationship("Sensor", secondary="sensor_location_association", back_populates="locations")

    # Обратная связь с Scenario
    scenarios = relationship("Scenario", back_populates="location", lazy="selectin")

    def __str__(self):
        return f"ID:{self.id} | {self.name}"


class SensorValue(Base):
    __tablename__ = "sensor_value"

    sensor_type = Column(String(255), doc="Тип датчика")
    field = Column(String(128), doc="Поле датчика")
    value = Column(String(64), doc="Значение")
    measurement = Column(String(64), doc="Величина измерения")


class Sensor(Base):
    __tablename__ = "sensor"

    KKS: Mapped[str] = mapped_column(String(64), nullable=False, doc="Код ККС")
    name: Mapped[str] = mapped_column(String(255), doc="Название датчика")

    # Связь с Model (один ко многим)
    model_id: Mapped[int] = mapped_column(ForeignKey("model.id"), nullable=False)
    model = relationship("Model", back_populates="sensors",
                         foreign_keys='Sensor.model_id',
                         lazy='selectin')

    # Связь с Location (многие ко многим через промежуточную таблицу)
    locations = relationship("Location", secondary="sensor_location_association", back_populates="sensors")

    # Связь с Scenario (многие к одному)
    scenarios = relationship("Scenario", back_populates="sensor")