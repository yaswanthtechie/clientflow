from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ProjectStatus = Literal["active", "archived"]


class ProjectCreate(BaseModel):
    client_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=255)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    name: str
    status: ProjectStatus
    created_at: datetime
