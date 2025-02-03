from typing import Optional, List, Union, Any
from pydantic import BaseModel

from typing import List, Dict, Any


class Lead(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    price: Optional[int] = None
    responsible_user_id: Optional[int] = None
    group_id: Optional[int] = None
    status_id: Optional[int] = None
    pipeline_id: Optional[int] = None
    loss_reason_id: Optional[int] = None
    source_id: Optional[int] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    closed_at: Optional[int] = None
    closest_task_at: Optional[int] = None
    custom_fields_values: Optional[Union[List[Any], None]] = None
    score: Optional[int] = None
    account_id: Optional[int] = None
    labor_cost: Optional[int] = None
    is_price_modified_by_robot: Optional[bool] = None

    class Config:
        extra = "forbid"

class LossReason(BaseModel):
    lead_id: Optional[int] = None
    id: Optional[int] = None
    name: Optional[str] = None
    sort: Optional[int] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    class Config:
        extra = "forbid"

class Tag(BaseModel):
    lead_id: Optional[int] = None
    id: Optional[int] = None
    name: Optional[str] = None
    color: Optional[str] = None

    class Config:
        extra = "forbid"

class Contact(BaseModel):
    lead_id: Optional[int] = None
    id: Optional[int] = None
    is_main: Optional[bool] = None

    class Config:
        extra = "forbid"

class Company(BaseModel):
    lead_id: Optional[int] = None
    id: Optional[int] = None

    class Config:
        extra = "forbid"

class CatalogElement(BaseModel):
    lead_id: Optional[int] = None
    id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    quantity: Optional[int] = None
    catalog_id: Optional[int] = None

    class Config:
        extra = "forbid"