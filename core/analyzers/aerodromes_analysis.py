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
from django.db.models import Q, QuerySet

from apps.aerodromes.models import Aerodrome
from apps.general.models.aircraft import Aircraft
from core.utils.regex_patterns import AERODROME


def _get_heliport_acceptable_types():
    return set(Aircraft.objects.filter(variant="Helicopter").values_list("type", flat=True))


def _check_flight_type_acceptable(ad: Aerodrome, ac_type: str, err: dict[str, list[str]]) -> None:
    HELIPORTS_ACCEPTABLE_AC_TYPES = _get_heliport_acceptable_types()
    if ad.type == "heliport" and ac_type not in HELIPORTS_ACCEPTABLE_AC_TYPES:
        err["logical_error"].append(f"{ad} is HELIPORT and isn't available for {ac_type}.")


def _check_aerodrome_operational_hours(
    aerodrome: Aerodrome,
    flight_datetime: datetime,
    flight_rule: str,
    err: dict[str, list[str]],
):
    flight_date = flight_datetime.date()
    flight_time = flight_datetime.time()

    op_hours = aerodrome.dailyoperationalhours.filter(date=flight_date)
    if op_hours.count() > 1:
        err["logical_error"].append(
            "Inform Administration: "
            f"More than one daily operational hours settings exists for {aerodrome} at date {flight_date}."
        )

    too_early_or_too_late = None

    too_early_or_too_late = op_hours.filter(
        Q(start_time__gt=flight_time) | Q(end_time__lt=flight_time)
    ).fist()
    if flight_rule == "VFR":
        too_early_or_too_late = op_hours.filter(
            Q(vfr_start_time__gt=flight_time) | Q(vfr_end_time__lt=flight_time)
        ).fist()

    if too_early_or_too_late is not None:
        msg = f"Your departure/arrival time {flight_time} at {aerodrome} is not in aerodrome's operational hours."
        if flight_rule == "VFR":
            msg += f"({too_early_or_too_late.vfr_start_time} & {too_early_or_too_late.vfr_end_time})."
        else:
            msg += f"({too_early_or_too_late.start_time} & {too_early_or_too_late.end_time})."

        if not aerodrome.aur:
            err["logical_error"].append(msg)
        else:
            err["warning"].append(msg + ", but this aerodrome is available upon request.")


def _check_aerodrome_temporarily_closure(
    aerodrome: Aerodrome, flight_datetime: datetime, err: dict[str, list[str]]
):
    temp_closures = list(
        aerodrome.temporaryclosures.filter(start__lte=flight_datetime, end__gte=flight_datetime)
    )

    for temp_closure in temp_closures:
        err["logical_error"].append(
            f"{aerodrome} is temporary closed, {temp_closure.start_time} till {temp_closure.end_time}."
        )


def _check_aerodrome_curfew(
    aerodrome: Aerodrome,
    flight_datetime: datetime,
    data_sts: str,
    data_rmk: str,
    err: dict[str, list[str]],
):
    curfews = list(aerodrome.curfews.filter(start__lte=flight_datetime, end__gte=flight_datetime))

    for curfew in curfews:
        if not any([True for sts in data_sts if sts in curfew.acceptable_sts]) or not any(
            [True for rmk in curfew.acceptable_rmk if rmk in data_rmk]
        ):
            err["logical_error"].append(f"{aerodrome} curfew time, {curfew.start} till {curfew.end}.")


def _analyse(
    aerodrome: Aerodrome,
    aircraft_type: str,
    flight_rule: str,
    flight_datetime: datetime,
    err: dict[str, list[str]],
    data_sts: str,
    data_rmk: str,
):
    _check_flight_type_acceptable(aerodrome, aircraft_type, err)
    _check_aerodrome_operational_hours(aerodrome, flight_datetime, flight_rule, err)
    _check_aerodrome_temporarily_closure(aerodrome, flight_datetime, err)
    _check_aerodrome_curfew(aerodrome, flight_datetime, data_sts, data_rmk, err)

    if flight_rule not in aerodrome.ifr_vfr:
        err["logical_error"].append(f"{aerodrome} does not accept {flight_rule.upper()}.")


def _get_aerodromes(indicators: list[str], err: dict[str, list[str]]) -> list[Union[Aerodrome, None]]:
    """getting dep, dest and alternate aerodromes"""

    aerodromes_qs: QuerySet[Aerodrome] = Aerodrome.objects.filter(indicator__in=indicators).prefetch_related(
        "dailyoperationalhours", "temporaryclosures", "curfews", "sid_stars"
    )

    # convert aerodromes to has-map to optimize db calls
    aerodromes_dict: dict[str, Aerodrome] = {aerodrome.indicator: aerodrome for aerodrome in aerodromes_qs}

    # To preserve the order according to the given indicators order
    aerodromes = list()

    for indicator in indicators:
        if indicator in ("ZZZZ", "AFIL", None) or indicator[:2] != settings.FIR_INDICATOR[:2]:
            # Indicator is not for a domestic aerodrome, so no need for futher checks so insert None
            aerodromes.append(None)
        elif indicator not in aerodromes_dict:
            # Seems indicator is miss spelled, unable to do further checks so insert None
            err["logical_error"].append(f"Aerodrome {indicator} does not exist.")
            aerodromes.append(None)
        else:
            aerodromes.append(aerodromes_dict.get(indicator, None))

    return aerodromes


def _sid_star_check(sid_star_name: str, type_: str, ad: Aerodrome, err: dict[str, list[str]]) -> None:
    sid_star = ad.sid_stars.filter(name=sid_star_name).first()
    if sid_star is None:
        err["logical_error"].append(f"{type_} {sid_star_name} does not exist.")
    else:
        if not sid_star.is_active:
            err["logical_error"].append(f"{type_} {sid_star_name} is not active.")

        if type_ not in sid_star.type:
            err["logical_error"].append(f"{sid_star_name}({sid_star.type}) is not of type {type_}.")


def aerodromes_analyzer(data: dict[str, Union[bool, str, list[dict[str, str]]]], err: dict[str, list[str]]):
    """Checks Related To Aerodromes"""

    if not all([data["departure_ad"], data["destination_ad"], data["alt_ad_1"]]):
        err["logical_error"].append(
            "The Destination, Departure and at least one Alternate Aerodromes are mandatory."
        )
        # if any of these is not found or active, then the rest of the checks could not be done!
        return

    flight_type = data["flight_type"]
    initial_flight_rule = "ifr" if data["flight_rule"] in "IY" else "vfr"
    last_flight_rule = "ifr" if data["route"][-1]["flight_rule"] in "IY" else "vfr"

    domestic_departure = data["domestic_departure"]
    domestic_destination = data["domestic_destination"]

    dep_datatime = datetime.datetime.strptime(data["dof"] + data["eobt"], "%y%m%d%H%M")
    est_arrival_datetime = dep_datatime + datetime.timedelta(
        hours=int(data["teet"][:2]), minutes=int(data["teet"][2:])
    )

    extra_ad_to_check = []
    for key in ("DEP", "DEST", "ALTN", "RALT", "TALT"):
        if key.lower() in data and (domestic_departure or domestic_destination):
            if re.match(AERODROME, data[key.lower()]) is not None:
                extra_ad_to_check.append(re.match(AERODROME, data[key.lower()]).groupdict().get("aerodrome"))

    aerodromes = _get_aerodromes(
        [data.get(key, None) for key in ("departure_ad", "destination_ad", "alt_ad_1", "alt_ad_2")]
        + extra_ad_to_check,
        err,
    )

    for aerodrome in aerodromes:
        if aerodrome is not None and not aerodrome.is_active:
            err["logical_error"].append(f"{aerodrome} is not active.")

    departure_ad, destination_ad, alt_ad_1, alt_ad_2, *other_alts = aerodromes

    if departure_ad is not None:
        _analyse(
            departure_ad,
            flight_type,
            initial_flight_rule,
            dep_datatime,
            err,
            data.get("sts", []),
            data.get("rmk", []),
        )

    for ad in (destination_ad, alt_ad_1, alt_ad_2, *other_alts):
        if ad is not None:
            _analyse(
                ad,
                flight_type,
                last_flight_rule,
                est_arrival_datetime,
                err,
                data.get("sts", []),
                data.get("rmk", []),
            )

    if departure_ad is not None:
        if domestic_departure and data.get("sid", None) is not None:
            _sid_star_check(data["sid"], "SID", departure_ad, err)

        if not domestic_destination and not (departure_ad.is_international and departure_ad.aur):
            err["logical_error"].append(
                f"Departure {departure_ad} is not international neither available upon request."
            )

    if destination_ad is not None:
        if domestic_destination and data.get("star", None) is not None:
            _sid_star_check(data["star"], "STAR", destination_ad, err)

        if not domestic_departure and not (destination_ad.is_international and destination_ad.aur):
            err["logical_error"].append(
                f"Destination {destination_ad} is not international neither available upon request."
            )
