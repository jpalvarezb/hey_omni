"""Input validation utilities."""
from typing import Any, Optional

def validate_input(text: str) -> bool:
    """Validate input text."""
    if not isinstance(text, str):
        return False
    if not text.strip():
        return False
    if len(text) > 1000:
        return False
    return True

def validate_json(data: Any) -> bool:
    """Validate JSON data."""
    if not data:
        return False
    try:
        import json
        json.dumps(data)
        return True
    except (TypeError, ValueError):
        return False
