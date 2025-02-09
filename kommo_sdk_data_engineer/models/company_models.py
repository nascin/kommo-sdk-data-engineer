from typing import Optional, Any
from pydantic import BaseModel

from typing import Optional, Dict, Any


class Company(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    responsible_user_id: Optional[int] = None
    group_id: Optional[int] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: Optional[int] = None  # Unix Timestamp
    updated_at: Optional[int] = None  # Unix Timestamp
    closest_task_at: Optional[int] = None  # Unix Timestamp, can be null
    account_id: Optional[int] = None

    class Config:
        extra = "forbid"


class CustomFieldValue(BaseModel):
    company_id: Optional[int] = None
    field_id: Optional[int] = None
    value: Optional[str] = None
    enum_id: Optional[int] = None
    enum_code: Optional[str] = None

    class Config:
        extra = "forbid"


class Tag(BaseModel):
    company_id: Optional[int] = None
    id: Optional[int] = None
    name: Optional[str] = None
    color: Optional[str] = None

    class Config:
        extra = "forbid"


class Contact(BaseModel):
    company_id: Optional[int] = None
    id: Optional[int] = None

    class Config:
        extra = "forbid"


class Lead(BaseModel):
    company_id: Optional[int] = None
    id: Optional[int] = None

    class Config:
        extra = "forbid"


class CatalogElement(BaseModel):
    company_id: Optional[int] = None
    id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    quantity: Optional[int] = None
    catalog_id: Optional[int] = None

    class Config:
        extra = "forbid"