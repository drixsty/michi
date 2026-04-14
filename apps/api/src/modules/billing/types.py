import strawberry
from datetime import datetime
from typing import Optional

@strawberry.type
class InvoiceType:
    id: str
    number: str
    amount: float
    currency: str
    status: str  # PAID, OPEN, VOID, UNCOLLECTIBLE
    date: datetime
    pdf_url: Optional[str] = None
    hosted_url: Optional[str] = None
