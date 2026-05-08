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
    attachments: List[TaskAttachment] = None  # List of file attachments
    is_archived: int = 0  # FT05: 0=active, 1=archived
    archived_at: Optional[str] = None  # FT05: ISO timestamp when archived
    deleted_at: Optional[str] = None  # FT05: ISO timestamp when soft-deleted to trash

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.attachments is None:
            self.attachments = []


@dataclass
class ActivityLog:
    id: Optional[int]
    task_id: Optional[int]
    task_title: str
    action: str
    details: str
    timestamp: datetime
    snapshot: Optional[str] = None  # JSON string of previous state for revert


@dataclass
class UserProfile:
    id: Optional[int]
    name: str
    email: Optional[str]
