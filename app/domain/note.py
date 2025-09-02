from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Tag:
    id: str
    name: str
    created_at: datetime
    updated_at: datetime

@dataclass
class Note:
    id: str
    user_id: str
    title: str
    content: str
    memo_date: str
    tags: list[Tag]
    created_at: datetime
    updated_at: datetime
    
    def change_title(self, new_title: str):
        if not new_title:
            raise ValueError("Title is required")
        self.title = new_title
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def change_content(self, new_content: str):
        if not new_content:
            raise ValueError("Content is required")
        self.content = new_content
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    def change_memo_date(self, new_memo_date: str):
        if not new_memo_date:
            raise ValueError("Memo date is required")
        self.memo_date = new_memo_date
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def change_tags(self, new_tags: list[Tag]):
        if not new_tags:
            raise ValueError("Tags are required")
        self.tags = new_tags
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def remove_all_tags(self):
        self.tags.clear()
    
