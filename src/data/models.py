from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from typing import List


@dataclass
class TaskAttachment:
    id: Optional[int]
    task_id: int
    file_path: str
    file_name: str


@dataclass
class Tag:
    id: Optional[int]
    name: str
    color: str


@dataclass
class Task:
    id: Optional[int]
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    due_date: Optional[datetime]
    priority: str
    is_deleted: int = 0
    color: str = "#FFFFFF"  # Default white HEX
    tags: List[Tag] = None  # List of associated tags
    attachments: List[TaskAttachment] = None  # NEW: List of file attachments

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.attachments is None:
            self.attachments = []


@dataclass
class UserProfile:
    id: Optional[int]
    name: str
    email: Optional[str]
