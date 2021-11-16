from .abstract import AerodromeProperties


class TemporaryClosure(AerodromeProperties):
    class Meta(AerodromeProperties.Meta):
        verbose_name = "Temporary Closure"
        verbose_name_plural = "Temporary Closures"
