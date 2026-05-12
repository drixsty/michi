from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELED = "CANCELED"
    INCOMPLETE = "INCOMPLETE"
    TRIALING = "TRIALING"

class BillingPlan(str, Enum):
    BASIC = "BASIC"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

@dataclass
class Invoice:
    id: str
    number: str
    amount: float
    currency: str
    status: str
    date: datetime
    pdf_url: Optional[str] = None
    hosted_url: Optional[str] = None

@dataclass
class Subscription:
    customer_id: str
    plan: BillingPlan
    status: SubscriptionStatus
    subscription_id: Optional[str] = None

@dataclass
class BillingPlanDefinition:
    id: str
    name: str
    price: float
    currency: str
    interval: str
    features: List[str]
    is_popular: bool = False
