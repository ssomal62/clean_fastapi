from pydantic import BaseModel, Field
from typing import Optional

class CreateNoteBody(BaseModel):
    title: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1)
    memo_date: str = Field(min_length=8, max_length=8)
    tag_names: Optional[list[str]] | None = Field(default=None, min_length=1, max_length=32)

class UpdateNoteBody(BaseModel):
    title: str | None = Field(min_length=1, max_length=64, default=None)
    content: str | None = Field(min_length=1, default=None)
    memo_date: str | None = Field(min_length=8, max_length=8, default=None)
    tag_names: Optional[list[str]] | None = Field(default=None, min_length=1, max_length=32)