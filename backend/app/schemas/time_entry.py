from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TimeEntryCreate(BaseModel):
    task_id: int = Field(gt=0)
    minutes: int = Field(gt=0, strict=True)
    worked_on: date


class TimeEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    minutes: int
    worked_on: date
    billed: bool
    created_at: datetime
