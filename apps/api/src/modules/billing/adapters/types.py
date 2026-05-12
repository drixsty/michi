import strawberry
from datetime import datetime
from typing import Optional

@strawberry.type
class InvoiceType:
    id: str
    number: str
    amount: float
    currency: str
    status: str
    date: datetime
    pdf_url: Optional[str] = None
    hosted_url: Optional[str] = None

@strawberry.type
class BillingPlanType:
    id: str
    name: str
    price: float
    currency: str
    interval: str
    features: list[str]
    is_popular: bool
