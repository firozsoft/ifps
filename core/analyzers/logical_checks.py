"""✘🗸"""
import datetime
from typing import Union

from core.analyzers import aerodromes_analysis, route_analysis


def logical_check(fpl: dict[str, Union[bool, str, list[dict[str, str]]]]):
    err: dict[str, list[str | None]] = {"logical_error": []}

    dep_datatime = datetime.datetime.strptime(fpl["dof"] + fpl["eobt"], "%y%m%d%H%M")
    if dep_datatime <= datetime.datetime.now() + datetime.timedelta(minutes=30):
        err["logical_error"].append("Submission of FPL within less than 30 minutes to EOBT is not allowed.")

    else:
        aerodromes_analysis.aerodromes_analyzer(fpl, err)
        route_analysis.route_analyzer(fpl, err)

    if err["logical_error"]:
        return {f"{inx}": err for inx, err in enumerate(err["logical_error"])}
