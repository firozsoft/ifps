"""Aerodromes Related Checks Module
    this module contains about:
        ✓ Aerodromes existence
        ✓ Aerodromes accept the flight regarding the flight Type
        ✓ Aerodromes accept the flight regarding the flight Rule
        ✓ Aerodromes accept the flight regarding the Ad. Internationality
        ✓ Aerodromes operational hours and curfews
        ✓ Aerodromes available upon request
        ✓ SID/STAR
"""

import datetime
import re
from typing import Union

from django.conf import settings
from django.db.models import Prefetch, Q, QuerySet

from apps.aerodromes.models import Aerodrome
from apps.aerodromes.models.curfew import Curfew
from apps.aerodromes.models.daily_opr import DailyOperationalHour
from apps.aerodromes.models.temp_closure import TemporaryClosure
from apps.general.models.aircraft import Aircraft
from apps.routes.models.sid_star import SidStar
from core.analyzers import error_messages
from core.utils import regex_patterns


def check_aerodrome_operational_hour(
    aerodrome: Aerodrome,
    flight_datetime: datetime,
    flight_rule: str,
    err: dict[str, list[str]],
):
    flight_date = flight_datetime.date()
    flight_time = flight_datetime.time()

    if len(aerodrome.dailyoperationalhours_list) > 1:
        err["logical_error"].append(
            error_messages.AERODROME_OPERATIONAL_HOURS_DUPLICATION.format(
                aerodrome, flight_date.strftime("%y%m%d")
            )
        )
        return

    if len(aerodrome.dailyoperationalhours_list) < 1:
        return

    today_operational_hours = aerodrome.dailyoperationalhours_list.pop()

    if flight_rule.upper() == "VFR":
        ad_start, ad_end = today_operational_hours.vfr_start_time, today_operational_hours.vfr_end_time
    else:
        ad_start, ad_end = today_operational_hours.start_time, today_operational_hours.end_time

    if ad_start <= flight_time <= ad_end:
        return

    flight_time, ad_start, ad_end = (
        flight_time.strftime("%H%m"),
        ad_start.strftime("%H%m"),
        ad_end.strftime("%H%m"),
    )
    if not aerodrome.aur:
        err["logical_error"].append(
            error_messages.AERODROME_TIME_UNACCEPTABLE.format(flight_time, aerodrome, ad_start, ad_end)
        )
    else:
        # TODO: instead of error there should be a RMK message that indicates AUR is coordinated.
        err["logical_error"].append(
            error_messages.AERODROME_TIME_UNACCEPTABLE_BUT_AUR.format(
                flight_time, aerodrome, ad_start, ad_end
            )
        )


def check_aerodrome_temporarily_closure(
    aerodrome: Aerodrome, flight_datetime: datetime, err: dict[str, list[str]]
):
    for temp_closure in aerodrome.temporaryclosures_list:
        if temp_closure.start <= flight_datetime <= temp_closure.end:
            err["logical_error"].append(
                error_messages.AERODROME_TEMP_CLOSURE.format(
                    aerodrome,
                    temp_closure.start.strftime("%y%m%d%H%M"),
                    temp_closure.end.strftime("%y%m%d%H%M"),
                )
            )


def check_aerodrome_curfew(
    aerodrome: Aerodrome, flight_datetime: datetime, data_sts: str, data_rmk: str, err: dict[str, list[str]]
):
    for curfew in aerodrome.curfews_list:
        if curfew.start <= flight_datetime <= curfew.end:
            if not any([True for sts in data_sts if sts in curfew.acceptable_sts]) or not any(
                [True for rmk in curfew.acceptable_rmk if rmk in data_rmk]
            ):
                err["logical_error"].append(
                    error_messages.AERODROME_CURFEW_TIME.format(
                        aerodrome, curfew.start.strftime("%y%m%d%H%M"), curfew.end.strftime("%y%m%d%H%M")
                    )
                )


def check_aerodrome_sid_star(
    sid_star_name: str, used_as_type: str, aerodrome: Aerodrome, err: dict[str, list[str]]
):
    found_sidstars = set()
    for sidstar in aerodrome.sid_stars_list:
        if sidstar.indicator == sid_star_name and sidstar.type == used_as_type:
            found_sidstars.add(sidstar)

    if len(found_sidstars) > 1:
        err["logical_error"].append(error_messages.SID_STAR_DUPLICATION.format(used_as_type, sid_star_name))
        return

    if len(found_sidstars) == 0:
        err["logical_error"].append(
            error_messages.SID_STAR_DOES_NOT_EXIST.format(used_as_type, sid_star_name)
        )
        return

    sid_star = found_sidstars.pop()
    if not sid_star.is_active:
        err["logical_error"].append(error_messages.SID_STAR_INACTIVE.format(sid_star))

    if not sid_star.nav_aid.is_active:
        err["logical_error"].append(
            error_messages.SID_STAR_NAVAID_INACTIVE.format(sid_star, sid_star.nav_aid)
        )

    if used_as_type not in sid_star.type:
        err["logical_error"].append(error_messages.SID_STAR_INCOMPATIBLE_TYPE.format(sid_star, used_as_type))


def analyse(
    aerodrome: Aerodrome,
    flight_rule: str,
    flight_datetime: datetime,
    aircraft_type: str,
    heliports_acceptable_types: set[str],
    err: dict[str, list[str]],
    data_sts: str,
    data_rmk: str,
):
    check_aerodrome_operational_hour(aerodrome, flight_datetime, flight_rule, err)
    check_aerodrome_temporarily_closure(aerodrome, flight_datetime, err)
    check_aerodrome_curfew(aerodrome, flight_datetime, data_sts, data_rmk, err)

    if aerodrome.type == "heliport" and aircraft_type not in heliports_acceptable_types:
        err["logical_error"].append(
            error_messages.AERODROME_INCOMPATIBLE_FLIGHT_TYPE.format(aerodrome, aerodrome.type, aircraft_type)
        )

    if flight_rule.lower() not in aerodrome.ifr_vfr.lower():
        err["logical_error"].append(
            error_messages.AERODROME_INCOMPATIBLE_FLIGHT_RULE.format(aerodrome, flight_rule.upper())
        )


def get_aerodrome_queryset(
    indicators: list[str],
    departure_datetime: datetime,
    est_arr_datetime: datetime,
    est_alt_arr_datetime: datetime,
    sid_star_names: list[str],
) -> QuerySet[Aerodrome]:
    """Fetching Aerodrome and it's related properties at once"""

    dailyoperationalhours_filtered_prefetch = Prefetch(
        "dailyoperationalhours",
        queryset=DailyOperationalHour.objects.filter(
            Q(date=departure_datetime.date())
            | Q(date=est_arr_datetime.date())
            | Q(date=est_alt_arr_datetime.date())
        ),
        to_attr="dailyoperationalhours_list",
    )
    temporaryclosures_filtered_prefetch = Prefetch(
        "temporaryclosures",
        queryset=TemporaryClosure.objects.filter(
            Q(start__lte=departure_datetime, end__gte=departure_datetime)
            | Q(start__lte=est_arr_datetime, end__gte=est_arr_datetime)
            | Q(start__lte=est_alt_arr_datetime, end__gte=est_alt_arr_datetime)
        ),
        to_attr="temporaryclosures_list",
    )
    curfews_filtered_prefetch = Prefetch(
        "curfews",
        queryset=Curfew.objects.filter(
            Q(start__lte=departure_datetime, end__gte=departure_datetime)
            | Q(start__lte=est_arr_datetime, end__gte=est_arr_datetime)
            | Q(start__lte=est_alt_arr_datetime, end__gte=est_alt_arr_datetime)
        ),
        to_attr="curfews_list",
    )
    sid_stars_filtered_prefetch = Prefetch(
        "sid_stars",
        queryset=SidStar.objects.filter(indicator__in=sid_star_names),
        to_attr="sid_stars_list",
    )

    aerodromes_qs: QuerySet[Aerodrome] = Aerodrome.objects.filter(indicator__in=indicators).prefetch_related(
        dailyoperationalhours_filtered_prefetch,
        temporaryclosures_filtered_prefetch,
        curfews_filtered_prefetch,
        sid_stars_filtered_prefetch,
    )

    return aerodromes_qs


def aerodromes_analyzer(fpl: dict[str, Union[bool, str, list[dict[str, str]]]], err: dict[str, list[str]]):
    """Checks Related To Aerodromes"""

    fpl["domestic_departure"] = True
    if not fpl["departure_ad"].startswith(settings.FIR_INDICATOR[:2]) or (
        "eet" in fpl.keys() and settings.FIR_INDICATOR in fpl["eet"]
    ):
        fpl["domestic_departure"] = False

    fpl["domestic_destination"] = True
    if not fpl["destination_ad"].startswith(settings.FIR_INDICATOR[:2]) or (
        "eet" in fpl.keys() and len(fpl["eet"].split(settings.FIR_INDICATOR)[1].strip()) > 4
    ):
        fpl["domestic_destination"] = False

    if not all([fpl["departure_ad"], fpl["destination_ad"], fpl["alt_ad_1"]]):
        err["logical_error"].append(error_messages.DEST_DEP_ONE_ALT_REQUIRED)
        # if any of these is not found or active, then the rest of the checks could not be done!
        return

    aircraft_type = fpl["aircraft_type"]
    initial_flight_rule = "ifr" if fpl["flight_rule"] in "IY" else "vfr"
    last_flight_rule = "ifr" if fpl["route"][-1]["flight_rule"] in "IY" else "vfr"

    domestic_departure = fpl["domestic_departure"]
    domestic_destination = fpl["domestic_destination"]

    heliports_acceptable_types = set(
        Aircraft.objects.filter(variant="Helicopter").values_list("type", flat=True)
    )
    heliports_acceptable_types.add("HEL")

    dep_datatime = datetime.datetime.strptime(fpl["dof"] + fpl["eobt"], "%y%m%d%H%M")
    est_arrival_datetime = dep_datatime + datetime.timedelta(
        hours=int(fpl["teet"][:2]), minutes=int(fpl["teet"][2:])
    )

    extra_ad_to_check = dict()
    for key in ("DEP", "DEST", "ALTN", "RALT", "TALT"):
        if key.lower() in fpl and (domestic_departure or domestic_destination):
            item18_ad = re.match(regex_patterns.AERODROME, fpl[key.lower()])
            if item18_ad is not None:
                extra_ad_to_check[key] = item18_ad.groupdict().get("aerodrome")

    indicators_to_fetch = {
        key: fpl[key] for key in ("departure_ad", "destination_ad", "alt_ad_1", "alt_ad_2") if key in fpl
    }

    indicators_to_fetch.update(extra_ad_to_check)

    est_alt_arr_datetime = est_arrival_datetime + datetime.timedelta(minutes=30)

    sid_star_names = [sid_star for sid_star in (fpl.get("star", None), fpl.get("sid", None)) if sid_star]

    exiting_aerodromes: dict[str, Aerodrome] = {
        aerodrome.indicator: aerodrome
        for aerodrome in get_aerodrome_queryset(
            set(indicators_to_fetch.values()),
            dep_datatime,
            est_arrival_datetime,
            est_alt_arr_datetime,
            sid_star_names,
        )
    }

    for indicator in indicators_to_fetch.values():
        if indicator not in exiting_aerodromes:
            err["logical_error"].append(error_messages.AERODROME_DOES_NOT_EXIST.format(indicator))

        elif not exiting_aerodromes[indicator].is_active:
            err["logical_error"].append(error_messages.AERODROME_INACTIVE.format(indicator))

    analyze_arguments = {
        "aircraft_type": aircraft_type,
        "heliports_acceptable_types": heliports_acceptable_types,
        "err": err,
        "data_sts": fpl.get("sts", []),
        "data_rmk": fpl.get("rmk", []),
    }

    departure_indicator = indicators_to_fetch.pop("departure_ad", None)
    departure_ad = exiting_aerodromes.get(departure_indicator, None)
    if departure_ad is not None:
        analyse(departure_ad, initial_flight_rule, dep_datatime, **analyze_arguments)

        if domestic_departure and fpl.get("sid", None) is not None:
            check_aerodrome_sid_star(fpl["sid"], "SID", departure_ad, err)

        if not domestic_destination and not (departure_ad.is_international and departure_ad.aur):
            err["logical_error"].append(
                error_messages.AERODROME_IS_NOT_INTERNATIONAL_NOR_AUR.format("Departure", departure_ad)
            )

    destination_indicator = indicators_to_fetch.pop("destination_ad", None)
    destination_ad = exiting_aerodromes.get(destination_indicator, None)
    if destination_ad is not None:
        analyse(destination_ad, last_flight_rule, est_arrival_datetime, **analyze_arguments)

        if domestic_destination and fpl.get("star", None) is not None:
            check_aerodrome_sid_star(fpl["star"], "STAR", destination_ad, err)

        if not domestic_departure and not (destination_ad.is_international and destination_ad.aur):
            # TODO: check if AUR is coordinated
            err["logical_error"].append(
                error_messages.AERODROME_IS_NOT_INTERNATIONAL_NOR_AUR.format("Destination", destination_ad)
            )

    for indicator in indicators_to_fetch.values():
        aerodrome = exiting_aerodromes.get(indicator, None)
        if aerodrome is not None:
            analyse(aerodrome, last_flight_rule, est_alt_arr_datetime, **analyze_arguments)
