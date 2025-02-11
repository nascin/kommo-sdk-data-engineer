from pydantic import BaseModel

from typing import Optional, Dict, Any


class PipelineModel(BaseModel):
    id: int
    name: Optional[str] = None
    sort: Optional[int] = None
    is_main: bool
    is_unsorted_on: bool
    is_archive: bool
    account_id: Optional[int] = None

    class Config:
        extra = "forbid"


class StatusModel(BaseModel):
    pipeline_id: int
    id: int
    name: Optional[str] = None
    sort: Optional[int] = None
    is_editable: bool
    color: Optional[str] = None
    type: Optional[int] = None
    account_id: Optional[int] = None