import re
from datetime import timedelta

from django import template

register = template.Library()


@register.filter
def format_timedelta(value):
    """Convert a timedelta object into a human-readable duration format.

    Example: 15 minutes, 2 hours and 30 minutes, etc.
    """
    if not isinstance(value, timedelta):
        return value

    seconds = value.total_seconds()
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours > 0:
        parts.append(f"{int(hours)} {'hour' if hours == 1 else 'hours'}")
    if minutes > 0:
        parts.append(f"{int(minutes)} {'minute' if minutes == 1 else 'minutes'}")

    return " and ".join(parts) if parts else "less than a minute"


@register.filter
def format_duration(iso_duration):
    """Convert an ISO 8601 duration string (e.g., PT15M) into a human-readable format."""
    if not isinstance(iso_duration, str):
        return iso_duration

    duration_regex = r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?$"
    match = re.match(duration_regex, iso_duration)

    if not match:
        return iso_duration  # Return the original string if it doesn't match the expected format

    hours = int(match.group("hours")) if match.group("hours") else 0
    minutes = int(match.group("minutes")) if match.group("minutes") else 0

    parts = []
    if hours > 0:
        parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
    if minutes > 0:
        parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")

    return " and ".join(parts) if parts else "less than a minute"
