from pydantic import BaseModel
from typing import Any, Dict


class ModelResponse(BaseModel):
    id: int
    model_type: str
    specification: Dict[str, Any]
    parameters: str

