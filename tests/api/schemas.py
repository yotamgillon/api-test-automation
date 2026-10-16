"""Response schemas used to validate API payloads (pydantic only, no extra dependency).

Strict mode and extra="forbid" make a wrong type or an unexpected key a failure.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class OrderSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    customer: str
    item: str
    quantity: int
    status: Literal["new", "paid", "shipped", "delivered", "cancelled"]


class ErrorSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    detail: str
