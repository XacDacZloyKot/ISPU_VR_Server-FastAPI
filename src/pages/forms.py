import re

from pydantic import BaseModel, field_validator
from src.auth.models import AdmissionStatus


class AdmissionUpdateForm(BaseModel):
    rating: str
    status: AdmissionStatus

    @field_validator('rating')
    def rating_validator(cls, value):
        pattern = r'^[0-5]\.[0-5]$'
        if re.match(pattern, value):
            return value
        raise ValueError('Оценка указана в неправильном виде! Правильный вид: 5.0, 2.5...')