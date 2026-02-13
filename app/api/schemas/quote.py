from pydantic import BaseModel


class QuoteRequest(BaseModel):
    from_currency: str
    to_currency: str
    amount: float

class QuoteResponse(BaseModel):
    quote_id: str
    rate: float
    estimated_amount: float
