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
    """Drop nonessential portions of fpl_route where exists

    The idea here is to walk trough the fpl route to reach a point that is not within the FIRs whom's
    indicators are mentioned in EET before our FIR indicator(incoming flights);
    or a point that is whithin (or in common with) the FIRs whom's indicators are mentioned in EET after
    our FIR indicator(for outgoing flights). index of section contaning such a point with regard to the
    incoming/outgoing (or "to"/"from" in section) is where the route portion have to be cutted out.
    """

    if neighbor_fir is None:
        err["logical_error"].append(
            errors.BOUNDARY_DETERMINATION_ERROR_NO_ADJACENT_FIRS.format(entry_or_exit, our_fir)
        )
        return []

    common_boundaries = set(our_fir.boundary_points).intersection(set(neighbor_fir.boundary_points))

    if not common_boundaries:
        err["logical_error"].append(
            errors.BOUNDARY_DETERMINATION_ERROR_NONADJACENT_FIR_OR_NO_BOUNDARY.format(neighbor_fir, our_fir)
        )
        return []

    fir_indicators = list(map(lambda string: string.strip()[:4], eet.split()))
    our_fir_indicator_index = fir_indicators.index(our_fir.indicator)

    previous_firs_indicators = set(fir_indicators[:our_fir_indicator_index])
    next_firs_indicators = set(fir_indicators[our_fir_indicator_index + 1 :])

    if entry_or_exit == "Entry":
        # in case of departures from adjacent FIRs they may omit Previous FIR in EET
        previous_firs_indicators.add(neighbor_fir.indicator)

    for index, section in enumerate(fpl_route):
        point_firs = existing_points.get(section["to"], None)
        if point_firs is not None:
            if entry_or_exit == "Entry" and not previous_firs_indicators.intersection(point_firs):
                if fpl_route[index]["via"] in ("", "DCT"):
                    continue
                return fpl_route[index:]

            if entry_or_exit == "Exit" and next_firs_indicators.intersection(point_firs):
                if fpl_route[index]["via"] in ("", "DCT"):
                    continue
                return fpl_route[: index + 1]
    else:
        err["logical_error"].append(errors.BOUNDARY_DETERMINATION_ERROR.format(entry_or_exit, our_fir))
        return []


def set_route_boundaries(
    route_portion_to_be_checked,
    existing_sections_dict,
    neighbor_fir,
    boundary_route_indicator,
    entry_or_exit,
    err,
):
    to_or_from = "from" if entry_or_exit == "Entry" else "to"

    possible_boundary_sections = {
        existing_sections_dict[tp] for tp in existing_sections_dict if tp[0] == boundary_route_indicator
    }

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
            route_portion_to_be_checked[(to_or_from == "to") * -1][to_or_from] = boundary_point.indicator
            # To provide data for route-scheme checks and avoid extra db querying
            route_portion_to_be_checked[(to_or_from == "to") * -1][
                f"{to_or_from}-fir"
            ] = neighbor_fir.indicator
            return route_portion_to_be_checked
    else:
        err["logical_error"].append(
            errors.BOUNDARY_DETERMINATION_ERROR_FROM_TO_FIR_ON_ROUTE.format(
                entry_or_exit, to_or_from, neighbor_fir, boundary_route_indicator
            )
        )
        return []


def normalize_route_portions(
    fpl, mentioned_points_in_fpl, route_portion_to_be_checked, err
) -> tuple[list[dict], dict[str, set[str]], dict[tuple, RouteSection]]:
    """Drops the unessential portion of flight planned route to our FIR and returns the
    normalized fpl route-sections list along with database route sections instances which are converted to
    dictionary to optimize database querying. Incases of failure to limiting the route the err dict gets
    updated with essential messages and two empty lists gets returned. if flight is domestic so the route gets
    no changes but the database sections will be fetched and returned along the unchanged route.

    - it's designed purposefully to have more python code specially multiple if statements on domestic
    departure/destination but to avoid multiple db hits and using cached data instead.
    """

    domestic_departure = fpl["domestic_departure"]
    domestic_destination = fpl["domestic_destination"]
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
                next_fir_indicator_2letters = "XQ"  # NOTE: FIR indicators can't be started with I,J,X,Q.
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
            all_existing_points[point.indicator] = all_existing_points.get(point.indicator, set()).union(
                [fir.indicator]
            )

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
                fpl["eet"],
                err,
            )
            if not route_portion_to_be_checked:
                # Without knowing entry point it's impossible to determine exit point.
                return [], [], []

        if not domestic_destination:
            route_portion_to_be_checked = get_essential_route_portion(
                our_fir,
                next_fir,
                route_portion_to_be_checked,
                all_existing_points,
                "Exit",
                fpl["eet"],
                err,
            )
            if not route_portion_to_be_checked:
                # Without knowing entry point it's impossible to determine exit point.
                return [], [], []

        entry_route_indicator = route_portion_to_be_checked[0]["via"]
        exit_route_indicator = route_portion_to_be_checked[-1]["via"]

    # up to here route_portion_to_be_checked only contains the routes which are crossing/within our FIR
    fpl_mentioned_routes = set(
        section["via"]
        for section in route_portion_to_be_checked
        if "nonessential" not in section or (section["via"] not in ("", "DCT"))
    )

    # All RouteSection instances of mentioned routes which are within our FIR
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
            entry_route_indicator,
            "Entry",
            err,
        )
        if not route_portion_to_be_checked:
            return [], [], []

    if not domestic_destination:
        route_portion_to_be_checked = set_route_boundaries(
            route_portion_to_be_checked,
            existing_sections_dict,
            next_fir,
            exit_route_indicator,
            "Exit",
            err,
        )
        if not route_portion_to_be_checked:
            return [], [], []

    if not existing_sections_dict:
        err["logical_error"].append(errors.ROUTE_PORTION_DETERMINATION_ERROR.format(our_fir))
        return [], [], []

    return route_portion_to_be_checked, all_existing_points, existing_sections_dict
