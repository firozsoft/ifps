from django.conf import settings
from django.db.models import Prefetch, Q

from apps.general.models.base import FIR
from apps.points.models import Point
from apps.routes.models import RouteSection
from core.analyzers import error_messages as errors


def get_essential_route_portion(
    our_fir: FIR,
    neighbor_fir: FIR,
    fpl_route: list[dict],
    existing_points: dict[str, set[str]],
    entry_or_exit: str,
    eet: str,
    err: dict,
):
    """
    Determine the essential portion of the flight route within our FIR.

    Args:
    - our_fir (FIR): Our FIR object.
    - neighbor_fir (FIR): Neighbor FIR object.
    - fpl_route (list[dict]): Flight route sections.
    - existing_points (dict): Existing points with FIR indicators.
    - entry_or_exit (str): Entry or Exit point.
    - eet (str): Estimated Elapsed Time (EET).
    - err (dict): Dictionary to store error messages.

    Returns:
    - list[dict]: Essential portion of the flight route.

    The idea here is to iterate over section of fpl route and check their to/from point's FIRs according to
    indicators that are mentioned in EET. The order of FIR indicators in EET is a key part here.

    - Drop sections up to the section that it's `to` point is within our-fir or firs after it.
    - Drop sections after the section that it's `to` point is within firs after our fir.

    - NOTE: In both case setion's `to` point is taken into account.
    """

    # Check if neighbor FIR is valid
    if neighbor_fir is None:
        err["logical_error"].append(
            errors.BOUNDARY_DETERMINATION_ERROR_NO_ADJACENT_FIRS.format(entry_or_exit, our_fir)
        )
        return []

    # Find common boundaries between our FIR and neighbor FIR
    common_boundaries = set(our_fir.boundary_points).intersection(set(neighbor_fir.boundary_points))
    if not common_boundaries:
        err["logical_error"].append(
            errors.BOUNDARY_DETERMINATION_ERROR_NONADJACENT_FIR_OR_NO_BOUNDARY.format(neighbor_fir, our_fir)
        )
        return []

    # Extract FIR indicators from EET
    fir_indicators = [indicator.strip()[:4] for indicator in eet.split()]
    our_fir_index = fir_indicators.index(our_fir.indicator)

    # Determine previous and next FIR indicators
    previous_firs_indicators = set(fir_indicators[:our_fir_index])
    next_firs_indicators = set(fir_indicators[our_fir_index + 1 :])

    # In case of departures from adjacent FIRs previous FIR indicator in EET may be omitted
    if entry_or_exit == "Entry":
        previous_firs_indicators.add(neighbor_fir.indicator)

    # Iterate over flight route sections to find essential portion
    for index, section in enumerate(fpl_route):
        point_firs = existing_points.get(section["to"], set())
        if entry_or_exit == "Entry" and not previous_firs_indicators.intersection(point_firs):
            if section["via"] not in ("", "DCT"):
                return fpl_route[index:]
        elif entry_or_exit == "Exit" and next_firs_indicators.intersection(point_firs):
            if section["via"] not in ("", "DCT"):
                return fpl_route[: index + 1]

    # No essential portion found, add error
    err["logical_error"].append(errors.BOUNDARY_DETERMINATION_ERROR.format(entry_or_exit, our_fir))
    return []


def set_route_boundaries(
    route_portion_to_be_checked,
    existing_sections_dict,
    neighbor_fir,
    entry_or_exit,
    err,
) -> list[dict]:
    """
    Set FIR boundaries for the flight planned route sections within our FIR.

    Args:
    - route_portion_to_be_checked (list[dict]): Route portion to be checked.
    - existing_sections_dict (dict): Existing route sections dictionary.
    - neighbor_fir (FIR): Neighbor FIR object.
    - entry_or_exit (str): Entry or Exit point.
    - err (dict): Dictionary to store error messages.

    Returns:
    - list[dict]: Route portion with boundaries set.

    Set `from` point of first section and `to` point of last section to FIR boundary points.

    Assuming given route_portion_to_be_checked is already limited to sections within or crossing our FIR,
    this function will attempt to set actual boundary points as initial/last points to the appropriate section
    the ideas is to use the common boundary points between two FIRs and the boundary route.
    """
    boundary_route_indicator, to_or_from = (
        (route_portion_to_be_checked[0]["via"], "from")
        if entry_or_exit == "Entry"
        else (route_portion_to_be_checked[-1]["via"], "to")
    )

    possible_boundary_sections = [
        existing_sections_dict[tp] for tp in existing_sections_dict if tp[0] == boundary_route_indicator
    ]

    if not possible_boundary_sections:
        err["logical_error"].append(errors.ROUTE_DOES_NOT_EXIST.format(boundary_route_indicator))
        return []

    for section in possible_boundary_sections:
        boundary_point = None
        if section.point1.is_fir_boundary and section.point1 in neighbor_fir.boundary_points:
            boundary_point = section.point1
        elif section.point2.is_fir_boundary and section.point2 in neighbor_fir.boundary_points:
            boundary_point = section.point2

        if boundary_point is not None:
            to_or_from_index = -1 if to_or_from == "to" else 0
            route_portion_to_be_checked[to_or_from_index][to_or_from] = boundary_point.indicator
            route_portion_to_be_checked[to_or_from_index][f"{to_or_from}-fir"] = neighbor_fir.indicator
            return route_portion_to_be_checked

    err["logical_error"].append(
        errors.BOUNDARY_DETERMINATION_ERROR_FROM_TO_FIR_ON_ROUTE.format(
            entry_or_exit, to_or_from, neighbor_fir, boundary_route_indicator
        )
    )
    return []


def normalize_route_portions(
    fpl: dict, mentioned_points_in_fpl: list[str], route_portion_to_be_checked: list[dict], err: dict
) -> tuple[list[dict], dict[str, set[str]], dict[tuple, RouteSection]]:
    """
    Normalize the flight planned route within our FIR.

    Args:
    - fpl (dict): Flight plan details.
    - mentioned_points_in_fpl (list[str]): Mentioned points in the flight plan.
    - route_portion_to_be_checked (list[dict]): Route portion to be checked.
    - err (dict): Dictionary to store error messages.

    Returns:
    - tuple: Tuple containing normalized route, existing points, and existing route sections.

    Drops the unessential portion of flight planned route to our FIR and returns the
    normalized FPL route-sections list along with database route sections instances which are converted to
    dictionary to optimize database querying. In cases of failure to limit the route, the err dict gets
    updated with essential messages and two empty lists are returned. If the flight is domestic, the route gets
    no changes but the database sections will be fetched and returned along with the unchanged route.

    - It's designed purposefully to have more Python code, especially multiple if statements on domestic
    departure/destination, to avoid multiple DB hits and use cached data instead.
    """

    domestic_departure = fpl.get("domestic_departure", False)
    domestic_destination = fpl.get("domestic_destination", False)
    our_fir_indicator_2letters = settings.FIR_INDICATOR[:2]

    firs_indicators_first_2letters = {our_fir_indicator_2letters}
    if fpl.get("eet", False):
        firs_indicators_first_2letters.update(eet.strip()[:2] for eet in fpl["eet"].split() if eet)

        if not domestic_departure:
            eets = fpl["eet"].split(settings.FIR_INDICATOR)
            try:
                previous_fir_indicator_2letters = eets[0].strip().split()[-1].strip()[:2]
            except IndexError:
                previous_fir_indicator_2letters = fpl["departure_ad"][:2]
            firs_indicators_first_2letters.add(previous_fir_indicator_2letters)

        if not domestic_destination:
            eets = fpl["eet"].split(settings.FIR_INDICATOR)
            try:
                next_fir_indicator_2letters = eets[1].strip().split()[1].strip()[:2]
            except IndexError:
                next_fir_indicator_2letters = "XQ"  # NOTE: FIR indicators can't start with I, J, X, Q.
            firs_indicators_first_2letters.add(next_fir_indicator_2letters)

    all_firs = FIR.objects.filter(
        Q(
            *[("indicator__startswith", first_2letters) for first_2letters in firs_indicators_first_2letters],
            _connector=Q.OR,
        )
    ).prefetch_related(
        Prefetch(
            "points",
            queryset=Point.objects.filter(is_fir_boundary=True),
            to_attr="boundary_points",
        ),
        Prefetch(
            "points",
            queryset=Point.objects.filter(indicator__in=mentioned_points_in_fpl),
            to_attr="all_points",
        ),
    )

    FIRs = {fir.indicator[:2]: fir for fir in all_firs}

    all_existing_points: dict[str, set[str]] = dict()
    for _, fir in FIRs.items():
        if not fir.is_active:
            err["logical_error"].append(errors.FIR_INACTIVE.format(fir))
        for point in fir.all_points:
            all_existing_points.setdefault(point.indicator, set()).add(fir.indicator)

    if not domestic_departure or not domestic_destination:
        our_fir = FIRs.get(our_fir_indicator_2letters, None)
        previous_fir = FIRs.get(previous_fir_indicator_2letters, None)
        next_fir = FIRs.get(next_fir_indicator_2letters, None)

        if not domestic_departure:
            route_portion_to_be_checked = get_essential_route_portion(
                our_fir,
                previous_fir,
                route_portion_to_be_checked,
                all_existing_points,
                "Entry",
                fpl.get("eet", ""),
                err,
            )
            if not route_portion_to_be_checked:
                # Unable to determine route portion
                return [], {}, {}

        if not domestic_destination:
            route_portion_to_be_checked = get_essential_route_portion(
                our_fir,
                next_fir,
                route_portion_to_be_checked,
                all_existing_points,
                "Exit",
                fpl.get("eet", ""),
                err,
            )
            if not route_portion_to_be_checked:
                # Unable to determine route portion
                return [], {}, {}

    fpl_mentioned_routes = {
        section["via"]
        for section in route_portion_to_be_checked
        if "nonessential" not in section or section["via"] not in ("", "DCT")
    }

    existing_sections = (
        RouteSection.objects.filter(
            Q(route__indicator__in=fpl_mentioned_routes)
            & (
                Q(point1__fir__indicator__startswith=our_fir_indicator_2letters)
                | Q(point2__fir__indicator__startswith=our_fir_indicator_2letters)
            )
        )
        .distinct()
        .select_related("route", "point1", "point2")
    )

    existing_sections_dict = {
        (sec.route.indicator, sec.point1.indicator, sec.point2.indicator): sec for sec in existing_sections
    }

    if not domestic_departure:
        route_portion_to_be_checked = set_route_boundaries(
            route_portion_to_be_checked,
            existing_sections_dict,
            previous_fir,
            "Entry",
            err,
        )
        if not route_portion_to_be_checked:
            # Unable to determine route portion
            return [], {}, {}

    if not domestic_destination:
        route_portion_to_be_checked = set_route_boundaries(
            route_portion_to_be_checked,
            existing_sections_dict,
            next_fir,
            "Exit",
            err,
        )
        if not route_portion_to_be_checked:
            # Unable to determine route portion
            return [], {}, {}

    if not existing_sections_dict:
        err["logical_error"].append(errors.ROUTE_PORTION_DETERMINATION_ERROR.format(our_fir))
        return [], {}, {}

    return route_portion_to_be_checked, all_existing_points, existing_sections_dict
