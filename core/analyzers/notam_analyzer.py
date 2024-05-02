import re

from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.aerodromes.models.aerodrome import Aerodrome
from apps.general.models.base import FIR
from apps.general.models.notam import Notam
from apps.routes.models.route_section import RouteSection


def notam_analyzer(
    fpl: dict[str, bool | str | list[dict[str, str]]],
    aerodromes: dict[str, Aerodrome],
    points: dict[str, set[str]],
    sections: dict[tuple, RouteSection],
    firs: dict[str, FIR],
    err: dict[str, list[str | None]],
) -> QuerySet[Notam]:
    dep_datetime = timezone.datetime.strptime(fpl["dof"] + fpl["eobt"], "%y%m%d%H%M")

    teet = fpl.get("teet")
    if not re.match(r"^\d{4}$", teet):
        err["integrity_error"].append("The TEET is not correct.")
        timedelta_hours, timedelta_minutes = 18, 20
    else:
        timedelta_hours, timedelta_minutes = int(teet[:2]), int(teet[2:])

    firs_indicators = {string[:4] for string in fpl.get("eet", "").split()}.union(firs.keys())

    return (
        Notam.objects.filter(is_active=True)
        .filter(
            Q(start__lte=dep_datetime - timezone.timedelta(hours=1))
            | Q(end__gte=dep_datetime + timezone.timedelta(hours=timedelta_hours, minutes=timedelta_minutes)),
        )
        .filter(
            Q(affected_aerodrome__indicator__in=aerodromes)
            | Q(affected_firs__indicator__in=firs_indicators)
            | Q(affected_points__indicator__in=points)
            | Q(affected_navaids__indicator__in=points)
            | Q(affected_sidstars__indicator__in=(fpl.get("sid", ""), fpl.get("star", "")))
            | Q(affected_route_sections__in=sections.values()),
        )
    )
