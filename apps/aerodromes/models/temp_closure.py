from .base import AerodromeProperties


class TemporaryClosure(AerodromeProperties):
    """An aerodrome may be temporarily closed for a certain date for a certain period of time"""

    class Meta(AerodromeProperties.Meta):
        verbose_name = "Temporary Closure"
        verbose_name_plural = "Temporary Closures"
