from pydantic_settings import BaseSettings, SettingsConfigDict


class NoteSettings(BaseSettings):
    """Note 도메인 설정"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # 노트 설정
    TITLE_MAX_LENGTH: int = 64
    CONTENT_MIN_LENGTH: int = 1
    MEMO_DATE_FORMAT: str = "YYYYMMDD"
    MEMO_DATE_LENGTH: int = 8
    
    # 태그 설정
    TAG_NAME_MAX_LENGTH: int = 32
    MAX_TAGS_PER_NOTE: int = 10

note_settings = NoteSettings()
