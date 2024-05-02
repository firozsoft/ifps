"""Aerodromes Related Checks Module.

this module contains about:
    ✓ Aerodromes existence
    ✓ Aerodromes accept the flight regarding the flight Type
    ✓ Aerodromes accept the flight regarding the flight Rule
    ✓ Aerodromes accept the flight regarding the Ad. Internationality
    ✓ Aerodromes operational hours and curfews
    ✓ Aerodromes available upon request
    ✓ SID/STAR
"""

import re

from django.conf import settings
from django.db.models import Prefetch, Q, QuerySet
from django.utils import timezone

from apps.aerodromes.models.aerodrome import Aerodrome
from apps.aerodromes.models.curfew import Curfew
from apps.aerodromes.models.daily_opr import DailyOperationalHour
from apps.aerodromes.models.temp_closure import TemporaryClosure
from apps.general.models.aircraft import Aircraft
from apps.routes.models.sid_star import SidStar
from core.utils import error_messages, patterns
from core.utils.choices import AerodromeFlightRule, AerodromeType


def check_aerodrome_operational_hour(
    aerodrome: Aerodrome,
    flight_datetime: timezone.datetime,
    flight_rule: str,
    err: dict[str, list[str]],
) -> None:
    """Check Temporary Closure related errors for the given aerodrome.

    Args:
    ----
        aerodrome (Aerodrome): The aerodrome to check.
        flight_datetime (timezone.datetime): The (estimated) date-time of flight within the aerodrome.
        flight_rule (str): The flight rule as indicated in flight plan within the aerodrome.
        err (Dict[str, List[str]]): Dictionary to store error messages.

    Returns:
    -------
        None

    """
    flight_date = flight_datetime.date()
    flight_time = flight_datetime.time()

    if len(aerodrome.dailyoperationalhours_list) > 1:
        err["integrity_error"].append(
            error_messages.AERODROME_OPERATIONAL_HOURS_DUPLICATION.format(
                aerodrome,
                flight_date.strftime("%y%m%d"),
            ),
        )
        return

    try:
        today_operational_hours = aerodrome.dailyoperationalhours_list[0]
    except IndexError:
        return

    if flight_rule == AerodromeFlightRule.VFR:
        op_start, op_end = today_operational_hours.vfr_start_time, today_operational_hours.vfr_end_time
    else:
        op_start, op_end = today_operational_hours.start_time, today_operational_hours.end_time

    if op_start <= flight_time <= op_end:
        return

    flight_time, op_start, op_end = (
        flight_time.strftime("%H%m"),
        op_start.strftime("%H%m"),
        op_end.strftime("%H%m"),
    )
    if not aerodrome.aur:
        err["integrity_error"].append(
            error_messages.AERODROME_TIME_UNACCEPTABLE.format(flight_time, aerodrome, op_start, op_end),
        )
    else:
        # TODO: instead of error there should be a RMK message that indicates AUR is coordinated.
        err["integrity_error"].append(
            error_messages.AERODROME_TIME_UNACCEPTABLE_BUT_AUR.format(
                flight_time,
                aerodrome,
                op_start,
                op_end,
            ),
        )


def check_aerodrome_temporarily_closure(
    aerodrome: Aerodrome,
    flight_datetime: timezone.datetime,
    err: dict[str, list[str]],
) -> None:
    """Check Temporary Closure related errors for the given aerodrome.

    Args:
    ----
        aerodrome (Aerodrome): The aerodrome to check.
        flight_datetime (timezone.datetime): The (estimated) date-time of flight within the aerodrome.
        err (Dict[str, List[str]]): Dictionary to store error messages.

    Returns:
    -------
        None

    """
    for temp_closure in aerodrome.temporaryclosures_list:
        if temp_closure.start <= flight_datetime <= temp_closure.end:
            err["integrity_error"].append(
                error_messages.AERODROME_TEMP_CLOSURE.format(
                    aerodrome,
                    temp_closure.start.strftime("%y%m%d%H%M"),
                    temp_closure.end.strftime("%y%m%d%H%M"),
                ),
            )


def check_aerodrome_curfew(
    aerodrome: Aerodrome,
    flight_datetime: timezone.datetime,
    data_sts: str,
    data_rmk: str,
    err: dict[str, list[str]],
) -> None:
    """Check Curfew related errors for the given aerodrome.

    Args:
    ----
        aerodrome (Aerodrome): The aerodrome to check.
        flight_datetime (timezone.datetime): The (estimated) date-time of flight within the aerodrome.
        data_sts (str): The STS of flight plan to be checked for Curfew related items.
        data_rmk (str): The RMK of flight plan to be checked for Curfew related items.
        err (Dict[str, List[str]]): Dictionary to store error messages.

    Returns:
    -------
        None

    """
    for curfew in aerodrome.curfews_list:
        if (
            curfew.start <= flight_datetime <= curfew.end
            and not any(True for sts in data_sts if sts in curfew.acceptable_sts)
            or not any(True for rmk in curfew.acceptable_rmk if rmk in data_rmk)
        ):
            err["integrity_error"].append(
                error_messages.AERODROME_CURFEW_TIME.format(
                    aerodrome,
                    curfew.start.strftime("%y%m%d%H%M"),
                    curfew.end.strftime("%y%m%d%H%M"),
                ),
            )


def check_aerodrome_sid_star(
    sid_star_name: str,
    used_as_type: str,
    aerodrome: Aerodrome,
    err: dict[str, list[str]],
) -> None:
    """Check SID/STAR related errors for the given aerodrome.

    Args:
    ----
        sid_star_name (str): The name of the SID/STAR.
        used_as_type (str): The type of SID/STAR used in FPL (SID or STAR).
        aerodrome (Aerodrome): The aerodrome to check.
        err (Dict[str, List[str]]): Dictionary to store error messages.

    Returns:
    -------
        None

    """
    found_sidstars = [
        sidstar
        for sidstar in aerodrome.sid_stars_list
        if sidstar.indicator == sid_star_name and used_as_type in sidstar.type
    ]

    if len(found_sidstars) > 1:
        err["integrity_error"].append(error_messages.SID_STAR_DUPLICATION.format(used_as_type, sid_star_name))
        return

    try:
        sid_star = found_sidstars[0]
    except IndexError:
        err["integrity_error"].append(
            error_messages.SID_STAR_DOES_NOT_EXIST.format(used_as_type, sid_star_name),
        )
        return
    if not sid_star.is_active:
        err["integrity_error"].append(error_messages.SID_STAR_INACTIVE.format(sid_star))

    if not sid_star.navaid.is_active:
        err["integrity_error"].append(
            error_messages.SID_STAR_NAVAID_INACTIVE.format(sid_star, sid_star.navaid),
        )


def analyse(
    aerodrome: Aerodrome,
    flight_rule: str,
    flight_datetime: timezone.datetime,
    type_of_aircraft: str,
    heliports_acceptable_types: set[str],
    err: dict[str, list[str]],
    data_sts: str,
    data_rmk: str,
) -> None:
    """Analyzes various aspects of the aerodrome for flight compatibility.

    Args:
    ----
        aerodrome (Aerodrome): The aerodrome to analyze.
        flight_rule (str): The flight rule (IFR or VFR).
        flight_datetime (timezone.datetime): The datetime of the flight.
        type_of_aircraft (str): The type of aircraft.
        heliports_acceptable_types (Set[str]): Acceptable types for heliports.
        err (Dict[str, List[str]]): Dictionary to store error messages.
        data_sts (str): Status information related to the flight.
        data_rmk (str): Remark information related to the flight.

    Returns:
    -------
        None

    """
    check_aerodrome_operational_hour(aerodrome, flight_datetime, flight_rule, err)

    check_aerodrome_temporarily_closure(aerodrome, flight_datetime, err)

    check_aerodrome_curfew(aerodrome, flight_datetime, data_sts, data_rmk, err)

    # Check if aircraft type is compatible with heliport
    if aerodrome.type == AerodromeType.HELIPORT and type_of_aircraft not in heliports_acceptable_types:
        err["integrity_error"].append(
            error_messages.AERODROME_INCOMPATIBLE_TYPE_OF_AIRCRAFT.format(
                aerodrome,
                aerodrome.type,
                type_of_aircraft,
            ),
        )

    # Check if flight rule is compatible with the aerodrome
    if flight_rule.lower() not in aerodrome.ifr_vfr.lower():
        err["integrity_error"].append(
            error_messages.AERODROME_INCOMPATIBLE_FLIGHT_RULE.format(aerodrome, flight_rule.upper()),
        )


def get_aerodrome_queryset(
    indicators: list[str],
    departure_datetime: timezone.datetime,
    est_arr_datetime: timezone.datetime,
    est_alt_arr_datetime: timezone.datetime,
    sid_star_names: list[str],
) -> QuerySet[Aerodrome]:
    """Retrieve Aerodrome queryset with related properties prefetched.

    Args:
    ----
        indicators (List[str]): List of aerodrome indicators.
        departure_datetime (timezone.datetime): Departure datetime.
        est_arr_datetime (timezone.datetime): Estimated arrival datetime.
        est_alt_arr_datetime (timezone.datetime): Estimated alternate arrival datetime.
        sid_star_names (List[str]): List of SID/STAR names.

    Returns:
    -------
        QuerySet[Aerodrome]: Aerodrome queryset with prefetched related properties.

    """
    # Filter Daily Operational Hours for relevant dates
    daily_operational_hours_filter = (
        Q(date=departure_datetime.date())
        | Q(date=est_arr_datetime.date())
        | Q(date=est_alt_arr_datetime.date())
    )
    daily_operational_hours_prefetch = Prefetch(
        "dailyoperationalhours",
        queryset=DailyOperationalHour.objects.filter(daily_operational_hours_filter),
        to_attr="dailyoperationalhours_list",
    )

    # Filter Temporary Closures for relevant datetime ranges
    temporary_closures_filter = (
        Q(start__lte=departure_datetime, end__gte=departure_datetime)
        | Q(start__lte=est_arr_datetime, end__gte=est_arr_datetime)
        | Q(start__lte=est_alt_arr_datetime, end__gte=est_alt_arr_datetime)
    )
    temporary_closures_prefetch = Prefetch(
        "temporaryclosures",
        queryset=TemporaryClosure.objects.filter(temporary_closures_filter),
        to_attr="temporaryclosures_list",
    )

    # Filter Curfews for relevant datetime ranges
    curfews_filter = (
        Q(start__lte=departure_datetime, end__gte=departure_datetime)
        | Q(start__lte=est_arr_datetime, end__gte=est_arr_datetime)
        | Q(start__lte=est_alt_arr_datetime, end__gte=est_alt_arr_datetime)
    )
    curfews_prefetch = Prefetch(
        "curfews",
        queryset=Curfew.objects.filter(curfews_filter),
        to_attr="curfews_list",
    )

    # Filter SID/STAR for provided names
    sid_star_filter = Q(indicator__in=sid_star_names)
    sid_star_prefetch = Prefetch(
        "sid_stars",
        queryset=SidStar.objects.filter(sid_star_filter),
        to_attr="sid_stars_list",
    )

    # Prefetch related properties and return aerodrome queryset
    return Aerodrome.objects.filter(indicator__in=indicators).prefetch_related(
        daily_operational_hours_prefetch,
        temporary_closures_prefetch,
        curfews_prefetch,
        sid_star_prefetch,
    )


def aerodromes_analyzer(  # noqa:C901
    fpl: dict[str, bool | str | list[dict[str, str]]],
    err: dict[str, list[str]],
) -> dict[str, Aerodrome]:
    """Analyzes aerodrome-related information.

    Args:
    ----
        fpl (dict): Flight plan information.
        err (dict): Dictionary to store error messages.

    Returns:
    -------
        dict[str, Aerodrome] | None

    """
    fpl["domestic_departure"] = True
    if not fpl["departure_ad"].startswith(settings.FIR_INDICATOR[:2]) or (
        "eet" in fpl and settings.FIR_INDICATOR in fpl["eet"]
    ):
        fpl["domestic_departure"] = False

    fpl["domestic_destination"] = True
    if not fpl["destination_ad"].startswith(settings.FIR_INDICATOR[:2]) or (
        "eet" in fpl and len(fpl["eet"].split(settings.FIR_INDICATOR)[1].strip()) > 4
    ):
        fpl["domestic_destination"] = False

    # Check if required aerodromes are provided
    if not all([fpl["departure_ad"], fpl["destination_ad"], fpl["alt_ad_1"]]):
        err["integrity_error"].append(error_messages.DEST_DEP_ONE_ALT_REQUIRED)
        return {}

    # Extract flight details
    type_of_aircraft = fpl["type_of_aircraft"]
    initial_flight_rule = "ifr" if fpl["flight_rule"] in "IY" else "vfr"
    last_flight_rule = "ifr" if fpl["route"][-1]["flight_rule"] in "IY" else "vfr"

    # Determine domestic departure and destination
    domestic_departure = fpl["domestic_departure"]
    domestic_destination = fpl["domestic_destination"]

    # Determine acceptable helicopter types
    heliports_acceptable_types = set(
        Aircraft.objects.filter(variant="Helicopter").values_list("type", flat=True),
    )
    heliports_acceptable_types.add("HEL")

    # Parse datetime information
    dep_datetime = timezone.datetime.strptime(fpl["dof"] + fpl["eobt"], "%y%m%d%H%M")
    est_arrival_datetime = dep_datetime + timezone.timedelta(
        hours=int(fpl["teet"][:2]),
        minutes=int(fpl["teet"][2:]),
    )

    # Extract additional aerodromes to check
    extra_ad_to_check = {}
    for key in ("DEP", "DEST", "ALTN", "RALT", "TALT"):
        if key.lower() in fpl and (domestic_departure or domestic_destination):
            item18_ad = re.match(patterns.AERODROME, fpl[key.lower()])
            if item18_ad is not None:
                extra_ad_to_check[key] = item18_ad.groupdict().get("aerodrome")

    # Create a dictionary of indicators to fetch
    indicators_to_fetch = {
        key: fpl[key]
        for key in ("departure_ad", "destination_ad", "alt_ad_1", "alt_ad_2")
        if key in fpl and fpl.get(key) is not None
    }

    indicators_to_fetch.update(extra_ad_to_check)

    # Calculate estimated alternate arrival datetime
    est_alt_arr_datetime = est_arrival_datetime + timezone.timedelta(minutes=60)

    # Extract SID/STAR names
    sid_star_names = [fpl[key] for key in ("star", "sid") if fpl.get(key)]

    # Retrieve aerodromes queryset
    exiting_aerodromes: dict[str, Aerodrome] = {
        aerodrome.indicator: aerodrome
        for aerodrome in get_aerodrome_queryset(
            set(indicators_to_fetch.values()),
            dep_datetime,
            est_arrival_datetime,
            est_alt_arr_datetime,
            sid_star_names,
        )
    }

    # Check for missing or inactive aerodromes
    for indicator in indicators_to_fetch.values():
        if indicator not in exiting_aerodromes:
            if indicator not in extra_ad_to_check.values() or indicator[:2] == settings.FIR_INDICATOR:
                err["integrity_error"].append(error_messages.AERODROME_DOES_NOT_EXIST.format(indicator))
        elif not exiting_aerodromes[indicator].is_active:
            err["integrity_error"].append(error_messages.AERODROME_INACTIVE.format(indicator))

    # Arguments for analysis
    analyze_arguments = {
        "type_of_aircraft": type_of_aircraft,
        "heliports_acceptable_types": heliports_acceptable_types,
        "err": err,
        "data_sts": fpl.get("sts", []),
        "data_rmk": fpl.get("rmk", []),
    }

    # Analyze departure aerodrome
    departure_indicator = indicators_to_fetch.pop("departure_ad", None)
    departure_ad = exiting_aerodromes.get(departure_indicator)
    if departure_ad is not None:
        analyse(departure_ad, initial_flight_rule, dep_datetime, **analyze_arguments)

        if domestic_departure and fpl.get("sid") is not None:
            check_aerodrome_sid_star(fpl["sid"], "SID", departure_ad, err)

        if not domestic_destination and not (departure_ad.is_international and departure_ad.aur):
            err["integrity_error"].append(
                error_messages.AERODROME_IS_NOT_INTERNATIONAL_NOR_AUR.format("Departure", departure_ad),
            )

    # Analyze destination aerodrome
    destination_indicator = indicators_to_fetch.pop("destination_ad", None)
    destination_ad = exiting_aerodromes.get(destination_indicator)
    if destination_ad is not None:
        analyse(destination_ad, last_flight_rule, est_arrival_datetime, **analyze_arguments)

        if domestic_destination and fpl.get("star") is not None:
            check_aerodrome_sid_star(fpl["star"], "STAR", destination_ad, err)

        if not domestic_departure and not (destination_ad.is_international and destination_ad.aur):
            # TODO: check if AUR is coordinated
            err["integrity_error"].append(
                error_messages.AERODROME_IS_NOT_INTERNATIONAL_NOR_AUR.format("Destination", destination_ad),
            )

    # Analyze alternate aerodromes
    for indicator in indicators_to_fetch.values():
        aerodrome = exiting_aerodromes.get(indicator)
        if aerodrome is not None:
            analyse(aerodrome, last_flight_rule, est_alt_arr_datetime, **analyze_arguments)

    return exiting_aerodromes
