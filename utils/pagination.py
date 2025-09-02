from datetime import datetime

def parse_cursor(cursor: str) -> tuple[datetime, str]:
    if cursor:
        parts = cursor.split("_")
        cursor_created_at = datetime.fromisoformat(parts[0])
        cursor_id = parts[1]
    else:
        cursor_created_at, cursor_id = None, None
    return cursor_created_at, cursor_id