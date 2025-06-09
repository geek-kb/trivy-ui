from datetime import datetime
import pytz
from app.core.config import settings


def format_timestamp(timestamp_str: str) -> str:
    """
    Format timestamp string to a consistent format.
    Handles both ISO format and Unix timestamps.

    Args:
        timestamp_str: Input timestamp string

    Returns:
        Formatted timestamp string in ISO format
    """
    try:
        # Try parsing as ISO format first
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        try:
            # Try parsing as Unix timestamp
            dt = datetime.fromtimestamp(float(timestamp_str))
        except (ValueError, TypeError):
            # If all parsing fails, return original string
            return timestamp_str

    # Convert to UTC
    utc_dt = dt.astimezone(pytz.UTC)
    return utc_dt.isoformat()
