"""
Utility functions for CloudOpsAI.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Get current UTC time with timezone information."""
    return datetime.now(timezone.utc)


def format_timestamp() -> str:
    """Format current UTC time as ISO 8601 string."""
    return get_utc_now().isoformat()


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary.

    Args:
        data (Dict[str, Any]): Dictionary to get value from
        key (str): Key to get
        default (Any): Default value if key not found

    Returns:
        Any: Value from dictionary or default
    """
    try:
        return data.get(key, default)
    except Exception as e:
        logger.error(f"Error getting key {key} from data: {str(e)}")
        return default
