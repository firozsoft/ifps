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
