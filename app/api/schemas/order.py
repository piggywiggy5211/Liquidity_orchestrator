from pydantic import BaseModel
from typing import Optional

class OrderCreateRequest(BaseModel):
    amount: float
    currency: str
    destination_address: str

class OrderResponse(BaseModel):
    id: str
    status: str
