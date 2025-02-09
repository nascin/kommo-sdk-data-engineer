from pydantic import BaseModel

from typing import Optional, Dict, Any


class CustomField(BaseModel):
    id: int
    name: Optional[str] = None
    code: Optional[str] = None
    sort: Optional[int] = None
    type: Optional[str] = None
    entity_type: str
    is_predefined: Optional[bool] = None
    is_deletable: Optional[bool] = None
    remind: Optional[str] = None
    is_api_only: Optional[bool] = None
    group_id: Optional[str] = None

    class Config:
        extra = "forbid"


class EnumValue(BaseModel):
    custom_field_id: int
    id: int
    value: str
    sort: int

    class Config:
        extra = "forbid"

class RequiredStatus(BaseModel):
    custom_field_id: int
    status_id: int
    pipeline_id: int

    class Config:
        extra = "forbid"