

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class PredictionRequest(BaseModel):
    id: int
    query: str


class PredictionResponse(BaseModel):
    id: int
    answer: Optional[int] = None
    reasoning: str
    sources: List[HttpUrl]