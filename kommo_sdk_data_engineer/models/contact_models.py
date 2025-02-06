from typing import Optional, List, Union, Any
from pydantic import BaseModel

from typing import List, Dict, Any


class Contact(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    responsible_user_id: Optional[int] = None
    group_id: Optional[int] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    closest_task_at: Optional[int] = None
    is_deleted: Optional[bool] = None
    is_unsorted: Optional[bool] = None
    account_id: Optional[int] = None

    class Config:
        extra = "forbid"


class CustomFieldValue(BaseModel):
    contact_id: Optional[int] = None
    field_id: Optional[int] = None
    value: Optional[str] = None
    enum_id: Optional[int] = None
    enum_code: Optional[str] = None

    class Config:
        extra = "forbid"

class Lead(BaseModel):
    contact_id: Optional[int] = None
    id: Optional[int] = None

    class Config:
        extra = "forbid"


class Tag(BaseModel):
    contact_id: Optional[int] = None
    id: Optional[int] = None
    name: Optional[str] = None
    color: Optional[str] = None

    class Config:
        extra = "forbid"


class Company(BaseModel):
    contact_id: Optional[int] = None
    id: Optional[int] = None

    class Config:
        extra = "forbid"


class CatalogElement(BaseModel):
    contact_id: Optional[int] = None
    id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    quantity: Optional[int] = None
    catalog_id: Optional[int] = None

    class Config:
        extra = "forbid"
