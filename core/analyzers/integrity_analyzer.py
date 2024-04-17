"""This module is the beginning of integrity checks.
This is the second step to analyze a flight plan message, after the parser module.
"""

from typing import Union

from core.analyzers import aerodromes_analyzer, route_analyzer


def main(
    fpl: dict[str, Union[bool, str, list[dict[str, str]]]],
) -> dict[str, Union[int, dict[str, list[Union[str, None]]]]]:
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
    err: dict[str, list[Union[str, None]]] = {"integrity_error": []}

    # Perform aerodromes analysis
    aerodromes_analyzer.aerodromes_analyzer(fpl, err)

    # Perform route analysis
    route_analyzer.route_analyzer(fpl, err)

    # Return any encountered errors
    if err["integrity_error"]:
        return {str(inx): err for inx, err in enumerate(err["integrity_error"])}
    else:
        return {}
