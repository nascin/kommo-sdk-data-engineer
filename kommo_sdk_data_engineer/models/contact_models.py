from typing import Optional, List, Union, Any
from pydantic import BaseModel

from typing import List, Dict, Any


class _ValueCustomField(BaseModel):
    value: Optional[str] = None
    enum_id: Optional[int] = None
    enum_code: Optional[str] = None
    
class _CustomFieldValue(BaseModel):
    field_id: Optional[int] = None
    values: Optional[Union[List[_ValueCustomField], None]] = None

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
    custom_fields_values: Optional[Union[List[_CustomFieldValue], None]] = None
    account_id: Optional[int] = None

    class Config:
        extra = "forbid"

class Lead(Contact):
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