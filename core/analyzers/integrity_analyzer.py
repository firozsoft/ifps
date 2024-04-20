"""This module is the beginning of integrity checks.
This is the second step to analyze a flight plan message, after the parser module.
"""

from collections import namedtuple

from core.analyzers import aerodromes_analyzer, notam_analyzer, route_analyzer


def integrity_checks(
    fpl: dict[str, bool | str | list[dict[str, str]]],
) -> dict[str, int | dict[str, list[str | None]]]:
    """
    Perform integrity checks on a flight plan and return any encountered errors.

    Args:
        fpl (dict): Flight plan dictionary containing information about the flight.

    Returns:
        dict: Dictionary containing any encountered errors, indexed by numbers.

    This function checks the flight plan for integrity errors, including:
    - Submission of FPL within less than 30 minutes to EOBT.
    - Analysis of aerodromes and routes using external analyzers.
    """
    err: dict[str, list[str | None]] = {"integrity_error": []}

    # Perform aerodromes analysis
    aerodromes = aerodromes_analyzer.aerodromes_analyzer(fpl, err)

    # Perform route analysis
    points, sections, firs = route_analyzer.route_analyzer(fpl, err)

    # Perform NOTAM analysis
    notams = notam_analyzer.notam_analyzer(fpl, aerodromes, points, sections, firs, err)

    # Return any encountered errors
    errors = (
        {str(inx): err for inx, err in enumerate(err["integrity_error"])} if err["integrity_error"] else {}
    )
    IntegrityCheck = namedtuple("IntegrityCheck", ("errors", "notams"))
    return IntegrityCheck(errors=errors, notams=notams)
