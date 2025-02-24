from typing import Optional, Dict, List
from pydantic import BaseModel


class Event(BaseModel):
    id: str
    type: str
    entity_id: int
    entity_type: str
    created_by: Optional[int] = None
    created_at: Optional[int] = None
    value_after: Optional[List] = None
    value_before: Optional[List] = None
    account_id: Optional[int] = None

    class Config:
        extra = "forbid"