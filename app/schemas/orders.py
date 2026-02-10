from pydantic import BaseModel
from typing import Optional

class OrderCreate(BaseModel):
    amount: float
    currency: str
    destination_address: str

class OrderResponse(BaseModel):
    id: str
    status: str

class QuoteRequest(BaseModel):
    from_currency: str
    to_currency: str
    amount: float

class QuoteResponse(BaseModel):
    quote_id: str
    rate: float
    estimated_amount: float
