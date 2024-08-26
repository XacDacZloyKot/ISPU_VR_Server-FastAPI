from pydantic import BaseModel
from typing import Any, Dict


class ModelResponse(BaseModel):
    id: int
    type_model: str
    specification: Dict[str, Any]
    parameters: str

