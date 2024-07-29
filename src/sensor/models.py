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
    Column('accident_id', Integer, ForeignKey('accident.id'))
)

# Промежуточная таблица для связи Many-to-Many между Location и Model
location_model_association = Table(
    'location_model_association',
    Base.metadata,
    Column('location_id', Integer, ForeignKey('location.id')),
    Column('model_id', Integer, ForeignKey('model.id'))
)


class Model(Base):
    __tablename__ = "model"

    specification = Column("specification", JSON, nullable=True)

    #  Создание связи ForeignKey
    sensor_type_id = Column(Integer, ForeignKey('sensortype.id'))
    # Связь объектов(ForeignKey)
    sensor_type = relationship("SensorType", back_populates="models", foreign_keys="Model.sensor_type_id",
                               lazy="selectin")
    #  Связь many to many(промежуточная таблица)
    accident = relationship("Accident", secondary=model_accident_association, back_populates="models",
                            lazy="subquery")
    locations = relationship("Location", secondary=location_model_association, back_populates="models",
                             lazy="subquery")
    #  Обратная совместимость
    scenarios = relationship("Scenario", back_populates="model", lazy="selectin")

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
    #  Связь many to many(промежуточная таблица)
    models = relationship("Model", secondary=model_accident_association, back_populates="accident",
                          lazy="subquery")
    scenarios = relationship("Scenario", secondary=scenario_accident_association, back_populates="accidents",
                             lazy="subquery")


class LocationStatus(Enum):
    DEVELOPING = "В разработке"
    INACTIVE = "Не доступна"
    COMPLETED = "Готова"


class Location(Base):
    __tablename__ = "location"

    name = Column(String(255), doc="Название локации")
    prefab = Column(String(300), doc="Путь до префаба")
    #  Связь many to many(промежуточная таблица)
    models = relationship("Model", secondary=location_model_association, back_populates="locations",
                          lazy="subquery")
    status: Mapped[LocationStatus] = mapped_column(SQLAEnum(LocationStatus), default=LocationStatus.DEVELOPING,
                                                    nullable=False, doc="Статус заявки")
    #  Обратная совместимость
    scenarios = relationship("Scenario", back_populates="location", lazy="selectin")

    def __str__(self):
        return f"ID:{self.id} | {self.name}"


class SensorValue(Base):
    __tablename__ = "sensor_value"

    sensor_type = Column(String(255), doc="Тип датчика")
    field = Column(String(128), doc="Поле датчика")
    value = Column(String(64), doc="Значение")
    measurement = Column(String(64), doc="Величина измерения")

