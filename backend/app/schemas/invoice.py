from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InvoiceCreate(BaseModel):
    client_id: int = Field(gt=0)
    time_entry_ids: list[int] = Field(min_length=1)

    @field_validator("time_entry_ids")
    @classmethod
    def validate_unique_time_entry_ids(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("Duplicate time entry IDs are not allowed")
        if any(entry_id <= 0 for entry_id in value):
            raise ValueError("Time entry IDs must be positive")
        return value


class InvoiceStatusUpdate(BaseModel):
    status: Literal["draft", "sent", "paid"]


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    total_cents: int
    status: Literal["draft", "sent", "paid"]
    created_at: datetime
