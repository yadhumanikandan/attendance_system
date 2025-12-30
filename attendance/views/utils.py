"""
Utility functions and decorators shared across views.
"""

from datetime import timedelta


def superuser_required(user):
    """Check if user is a superuser."""
    return user.is_superuser


def parse_duration(duration_str):
    """Parse duration string like 'HH:MM:SS' to timedelta."""
    if not duration_str or duration_str == '':
        return timedelta(0)
    try:
        parts = str(duration_str).split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return timedelta(minutes=minutes, seconds=seconds)
    except (ValueError, AttributeError):
        pass
    return timedelta(0)
