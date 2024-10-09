from django.db.models import QuerySet

from apps.general.models.notam import Notam
from core.analyzers import aerodromes_analyzer, notam_analyzer, route_analyzer, route_schemes_analyzer


def integrity_checks(
    fpl: dict[str, bool | str | list[dict[str, str]]],
) -> tuple[dict[str, str | None], QuerySet[Notam]]:
    """Perform integrity checks on a flight plan and return any encountered errors.

    Args:
    ----
        fpl (dict): Flight plan dictionary containing information about the flight.

    Returns:
    -------
        dict: Dictionary containing any encountered errors, indexed by numbers.
        queryset: QuerySet containing any NOTMAs.

    This function checks the flight plan for integrity errors, including:
    - Submission of FPL within less than 30 minutes to EOBT.
    - Analysis of aerodromes and routes using external analyzers.

    """
    err: dict[str, list[str | None]] = {"integrity_error": []}

    # Perform aerodromes analysis
    aerodromes = aerodromes_analyzer.aerodromes_analyzer(fpl, err)

    # Perform route analysis
    points, sections, firs, route = route_analyzer.route_analyzer(fpl, err)

    # Check route-scheme (TOS) adherence
    route_schemes_analyzer.route_schemes_analyzer(fpl, route, err)

    notams = Notam.objects.none()
    if not err["integrity_error"]:
        # Perform NOTAM analysis
        notams = notam_analyzer.notam_analyzer(fpl, aerodromes, points, sections, firs, err)

    # Return any encountered errors
    errors = (
        {str(inx): err for inx, err in enumerate(err["integrity_error"])} if err["integrity_error"] else {}
    )

    return errors, notams
