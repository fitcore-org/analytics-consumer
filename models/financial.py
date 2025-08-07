from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal

@dataclass
class Expense:
    id: str
    amount: Decimal
    description: str
    expense_date: datetime
    created_at: Optional[datetime] = None

@dataclass
class Revenue:
    id: str
    amount: Decimal
    description: str
    revenue_date: datetime
    created_at: Optional[datetime] = None

@dataclass
class Profit:
    id: str
    period_start: datetime
    period_end: datetime
    total_revenue: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    profit_margin: float
    created_at: datetime
