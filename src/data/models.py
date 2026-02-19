
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Task:
    id: Optional[int]
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    due_date: Optional[datetime]
    priority: str

@dataclass
class UserProfile:
    id: Optional[int]
    name: str
    email: Optional[str]
