from dataclasses import dataclass
from datetime import datetime, timezone

from .settings import note_settings


@dataclass
class Tag:
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if len(self.name) > note_settings.TAG_NAME_MAX_LENGTH:
            raise ValueError(f"Tag name cannot exceed {note_settings.TAG_NAME_MAX_LENGTH} characters")

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
        if len(new_title) > note_settings.TITLE_MAX_LENGTH:
            raise ValueError(f"Title cannot exceed {note_settings.TITLE_MAX_LENGTH} characters")
        self.title = new_title
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def change_content(self, new_content: str):
        if not new_content:
            raise ValueError("Content is required")
        if len(new_content) < note_settings.CONTENT_MIN_LENGTH:
            raise ValueError(f"Content must be at least {note_settings.CONTENT_MIN_LENGTH} character")
        self.content = new_content
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    def change_memo_date(self, new_memo_date: str):
        if not new_memo_date:
            raise ValueError("Memo date is required")
        if len(new_memo_date) != note_settings.MEMO_DATE_LENGTH:
            raise ValueError(f"Memo date must be {note_settings.MEMO_DATE_LENGTH} characters")
        self.memo_date = new_memo_date
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def change_tags(self, new_tags: list[Tag]):
        if len(new_tags) > note_settings.MAX_TAGS_PER_NOTE:
            raise ValueError(f"Maximum {note_settings.MAX_TAGS_PER_NOTE} tags allowed per note")
        self.tags = new_tags
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def remove_all_tags(self):
        self.tags.clear()
    
