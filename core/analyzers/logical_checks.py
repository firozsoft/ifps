import datetime
from typing import Union

from core.analyzers import aerodromes_analysis, route_analysis


def logical_check(
    fpl: dict[str, Union[bool, str, list[dict[str, str]]]],
) -> dict[str, Union[int, dict[str, list[Union[str, None]]]]]:
    """
    Perform logical checks on a flight plan and return any encountered errors.

    Args:
        fpl (dict): Flight plan dictionary containing information about the flight.

    Returns:
        dict: Dictionary containing any encountered errors, indexed by numbers.

    This function checks the flight plan for logical errors, including:
    - Submission of FPL within less than 30 minutes to EOBT.
    - Analysis of aerodromes and routes using external analyzers.
    """
    err: dict[str, list[Union[str, None]]] = {"logical_error": []}

    # Ensure default date of flight is set to today if not provided
    fpl["dof"] = fpl.get("dof", datetime.datetime.today().strftime("%y%m%d"))

    # Calculate departure datetime
    dep_datatime = datetime.datetime.strptime(fpl["dof"] + fpl["eobt"], "%y%m%d%H%M")

    # Check if FPL submission occurs at least 30 minutes before EOBT
    if datetime.datetime.now() + datetime.timedelta(minutes=30) <= dep_datatime:
        err["logical_error"].append("Submission of FPL within less than 30 minutes to EOBT is not allowed.")
    else:
        # Perform aerodromes analysis
        aerodromes_analysis.aerodromes_analyzer(fpl, err)

        # Perform route analysis
        route_analysis.route_analyzer(fpl, err)

    # Return any encountered errors
    if err["logical_error"]:
        return {str(inx): err for inx, err in enumerate(err["logical_error"])}
    else:
        return {}
