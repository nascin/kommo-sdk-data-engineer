from pydantic import BaseModel

from typing import Optional


class User(BaseModel):
    id: int
    name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        extra = "forbid"
