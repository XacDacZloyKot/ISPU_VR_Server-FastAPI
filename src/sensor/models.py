from sqlalchemy import Table, String, MetaData, Column, Integer, JSON, Text


metadata = MetaData()


model = Table(
    "model",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sensor_type", String(255), nullable=False),
    Column("specification", JSON, nullable=True),
    Column("parameters", Text, nullable=True),
)
