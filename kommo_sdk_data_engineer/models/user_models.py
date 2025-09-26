from pydantic import BaseModel

from typing import Optional


class User(BaseModel):
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    group_id: Optional[int] = None

    class Config:
        extra = "forbid"


class Group(BaseModel):
    id: int
    name: Optional[str] = None
    user_id: int

    class Config:
        extra = "forbid"