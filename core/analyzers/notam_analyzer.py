import datetime as dt

from django.db.models import Q, QuerySet

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
    dep_datetime = dt.datetime.strptime(fpl["dof"] + fpl["eobt"], "%y%m%d%H%M")
    try:
        timedelta_hours, timedelta_minutes = int(fpl.get("teet")[:2]), int(fpl.get("teet")[2:])
    except Exception:
        err["integrity_error"].append("The TEET is not correct.")
        timedelta_hours, timedelta_minutes = 18, 20

    firs_indicators = set([string[:4] for string in fpl.get("eet", "").split()]).union(firs.keys())

    considerable_notams = (
        Notam.objects.filter(is_active=True)
        .filter(
            Q(start__lte=dep_datetime - dt.timedelta(hours=1))
            | Q(end__gte=dep_datetime + dt.timedelta(hours=timedelta_hours, minutes=timedelta_minutes))
        )
        .filter(
            Q(affected_aerodrome__indicator__in=aerodromes)
            | Q(affected_firs__indicator__in=firs_indicators)
            | Q(affected_points__indicator__in=points)
            | Q(affected_navaids__indicator__in=points)
            | Q(affected_sidstars__indicator__in=(fpl.get("sid", ""), fpl.get("star", "")))
            | Q(affected_route_sections__in=sections.values())
        )
    )

    return considerable_notams
