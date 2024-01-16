import re
from datetime import datetime
from typing import Union

from django.core.exceptions import ValidationError

from core.utils import regex_patterns
from core.utils.patterns import OTHER_INFO_SWITCHES


def _update_segments(segment_list: list[dict[str, str]], to: str):
    segment_list[-1]["to"] = to
    # NOTO: Don't try to be smart here! creating a new_segment like: `new_segment = segment_list[-1]`
    # then `In python` it will point to the same object (segment_list[-1]) not a new copy of it! use copy.deepcopy !!
    segment_list.append(
        {
            "from": to,
            "to": "",
            "via": "",
            "speed": segment_list[-1]["speed"],
            "level": segment_list[-1]["level"],
            "top_level": segment_list[-1]["top_level"],
            "flight_rule": segment_list[-1]["flight_rule"],
        }
    )


def _check_and_handle_possible_speed_level_change(pattern, matched, segments):
    if pattern in (regex_patterns.CHANGE_SPEED_LEVEL, regex_patterns.CRUISE_CLIMB):
        segments[-1]["speed"] = matched.groupdict().get("speed")
        segments[-1]["level"] = matched.groupdict().get("level")
        if pattern == regex_patterns.CRUISE_CLIMB:
            segments[-1]["top_level"] = matched.groupdict().get("top_level")
        else:
            segments[-1]["top_level"] = segments[-1]["level"]


def _check_item_is_valid_point_with_indicator(item, previous, segments, err):
    matched_pattern = None
    for pattern in (regex_patterns.CHANGE_SPEED_LEVEL, regex_patterns.CRUISE_CLIMB, regex_patterns.POINT):
        if (matched := re.match(pattern, item)) is not None:
            matched_pattern = pattern
            break
    else:
        err["syntax_error"].append(f"Item {item} (after {previous['item']}) must be a valid point.")
        return

    if matched.groupdict().get("point") is None:
        err["syntax_error"].append(f"Item {item} must be a valid point Indicator not a location.")
        return

    if previous["type"] == "sid" and previous["item"][:-2] not in (
            matched.groupdict().get("point"),
            # to accept if they forget the last char of the point name in sid/star
            matched.groupdict().get("point")[:-1],
    ):
        err["syntax_error"].append(f"Point {item} doesn't match with SID {previous['item']}.")

    # now we can reassign the variable previous to new data
    previous = {"type": "point", "item": matched.groupdict().get("point")}

    _check_and_handle_possible_speed_level_change(matched_pattern, matched, segments)

    return previous


def _check_item_is_valid_point_or_location(item, previous, res, segments, err):
    matched_pattern = None
    for pattern in (regex_patterns.CHANGE_SPEED_LEVEL, regex_patterns.CRUISE_CLIMB, regex_patterns.SIG_POINT):
        if (matched := re.match(pattern, item)) is not None:
            matched_pattern = pattern
            break
    else:
        err["syntax_error"].append(f"{item} (after {previous['item']}) must be a valid Significant point.")
        return

    if matched.groupdict().get("location"):
        previous = {"type": "location", "item": matched.groupdict().get("location")}
        segments[-1]["section_doesnt_need_check"] = True
        if matched.groupdict().get("ref_point"):
            res["ref_points"].append(matched.groupdict().get("ref_point"))
            # TODO: check if the line below is required ro delete it
            # segments[-1].pop("section_doesnt_need_check", None)

    elif matched.groupdict().get("point"):
        previous = {"type": "point", "item": matched.groupdict().get("point")}

    _check_and_handle_possible_speed_level_change(matched_pattern, matched, segments)

    return previous


def _check_item_is_valid_route_or_dct_or_ifr_vfr(item, previous, res, segments, err):
    if (matched := re.match(regex_patterns.SID_STAR, item)) is not None:
        if matched.groupdict().get("point") not in (
                previous["item"],
                previous["item"][:-1],  # to accept if they forget the last char of the point name in sid/star
        ):
            err["syntax_error"].append(f"Point {previous['item']} doesn't match with STAR {item}.")

        else:
            previous = {"type": "route", "item": (star := matched.groupdict().get("sid_star"))}
            segments[-1]["via"] = star
            res["star"] = star

    elif matched := re.match(regex_patterns.ROUTE, item):
        previous = {"type": "route", "item": (route := matched.groupdict().get("route"))}
        segments[-1]["via"] = route

    elif item == "DCT":
        previous = {"type": "dct", "item": "DCT"}
        segments[-1]["via"] = "DCT"
        segments[-1]["section_doesnt_need_check"] = True

    elif item in ("IFR", "VFR") and re.match(regex_patterns.CHANGE_FLT_RULE, f"{previous['item']} {item}"):
        if res["flight_rule"] not in ("Y", "Z"):
            err["syntax_error"].append(
                f"Illegal change of flight rule (after {previous['item']}) initial one was not 'Y' or 'Z'."
            )

        if segments[-1]["flight_rule"] == item[0]:
            err["syntax_error"].append(
                f"{item} (after {previous['item']}) is Incorrect change of flight rule. {item} to {item}."
            )

        else:
            segments[-1]["flight_rule"] = item[0]
    else:
        err["syntax_error"].append(
            f"{item} (after {previous['item']}) must be a Route or DCT or Change of flight rule (IFR/VFR)."
        )
        return

    return previous


def route_regex_parse(
        data: dict[str, str],
        res: dict[str, Union[str, list[dict[str, str]]]],
        err: dict[str, list[str]],
):
    """Checks for syntax errors in route part of a fpl msg"""

    # Flight Plan Route (Item 15)
    # The first cruising speed as in (a) and the first cruising level, then for:
    # 1- Flight inside controlled airspace
    # ((Sid | Route) | (DCT Point Route)) ((Point | ChangeSpeedLevel | (Point ChangeFltRule)) (Route | DCT))+ Point Star?
    # 2- Flight outside controlled airspace
    # (Point DCT? Point)+

    route_items: list[str] = data["route"].split()
    if (init_sp_lvl := re.match(regex_patterns.SPEED_LEVEL, route_items[0])) is not None:
        res["initial_speed"] = init_sp_lvl.groupdict().get("speed")
        res["initial_level"] = init_sp_lvl.groupdict().get("level")

    else:
        err["syntax_error"].append(f"{route_items[0]} must be a valid speed & level.")

    # keep a look at item already checked to be able to expect the nature of next item to be checked
    previous: dict[str, str] = {"type": "", "item": ""}

    # route_items[1] must be DCT, Route or Point
    if route_items[1] == "DCT":
        previous = {"type": "dct", "item": "DCT"}

    elif item := re.match(regex_patterns.ROUTE, route_items[1]):
        previous = {"type": "route", "item": item.groupdict().get("route")}

    elif item := re.match(regex_patterns.SID_STAR, route_items[1]):
        previous = {"type": "sid", "item": item.groupdict().get("sid_star")}
        res["sid"] = item.groupdict().get("sid_star")

    elif item := re.match(regex_patterns.POINT, route_items[1]):
        previous = {"type": "point", "item": item.groupdict().get("point")}

    elif item := re.match(regex_patterns.LOCATION, route_items[1]):
        previous = {"type": "location", "item": item.groupdict().get("location")}
        if item.groupdict().get("ref_point"):
            res["ref_points"].append(item.groupdict().get("ref_point"))

    else:
        err["syntax_error"].append(f"{route_items[1]} must be a valid ATS Route or DCT or an ATS Point")
        return

    # route segments
    segments: list[dict[str, str]] = [
        {
            "from": res["departure_ad"],
            "to": previous["item"] if previous["type"] in ("point", "location") else "",
            "via": previous["item"] if previous["type"] in ("route", "dct", "sid") else "",
            "speed": res["initial_speed"],
            "level": res["initial_level"],
            "top_level": res["initial_level"],
            "flight_rule": "I" if res["flight_rule"] in ("I", "Y") else "V",
        }
    ]

    rest_of_route_items = route_items[2:]
    set_rest_of_route_items = set(rest_of_route_items)

    needs_change_of_flt_rule = res["flight_rule"] in ("Z", "Y")
    if needs_change_of_flt_rule:
        if res["flight_rule"] == "Z" and "IFR" not in set_rest_of_route_items:
            err["syntax_error"].append(
                f"Flight rule is filled as {res['flight_rule']} but doesn't changed (to IFR) in the route."
            )
        if res["flight_rule"] == "Y" and "VFR" not in set_rest_of_route_items:
            err["syntax_error"].append(
                f"Flight rule is filled as {res['flight_rule']} but doesn't changed (to VFR) in the route."
            )

    # previous['type'] == 'route' | 'dct' | 'point' | 'location'
    for item in rest_of_route_items:
        # NOTE: _update_segments must only be called if item is a SIG_POINT not for DCT or ROUTE or IFR/VFR or etc.
        if previous["type"] in ("route", "sid"):
            # current item can be a point that has an assigned indicator (point, change speed-level, cruise-climb)
            previous = _check_item_is_valid_point_with_indicator(item, previous, segments, err)
            if previous is not None:
                _update_segments(segments, previous["item"])
            else:
                return
            continue
        if previous["type"] == "dct":
            # current item can be a sig-point
            previous = _check_item_is_valid_point_or_location(item, previous, res, segments, err)
            if previous is not None:
                _update_segments(segments, previous["item"])
            else:
                return
            continue
        if previous["type"] == "point":
            # current item can be a route or dct or IFR/VFR
            previous = _check_item_is_valid_route_or_dct_or_ifr_vfr(item, previous, res, segments, err)
            if previous is None:
                return
            continue
        if previous["type"] == "location":
            # current item can be a location or dct => this means there's no predefined route section used here
            segments[-1]["section_doesnt_need_check"] = True
            if item == "DCT":
                previous = {"type": "dct", "item": "DCT"}
                segments[-1]["via"] = "DCT"
                segments[-1]["section_doesnt_need_check"] = True
            elif matched := re.match(regex_patterns.LOCATION, item):
                previous = {"type": "location", "item": matched.groupdict().get("location")}
                _update_segments(segments, previous["item"])
                segments[-1]["section_doesnt_need_check"] = True
            else:
                err["syntax_error"].append(
                    f"{item} (after {previous['item']}) must be a valid Sig.Point or word DCT."
                )
            continue

    segments[-1]["to"] = res["destination_ad"]

    res["route"] = segments


def regex_parse(
        row_data: dict[str, str],
) -> tuple[dict[str, Union[str, list[dict[str, str]]]], Union[ValidationError, None]]:
    """Checks for syntax errors and prepares a new dict"""
    regex_parsed_data = dict()
    validation_error = None
    err: dict[str, list[str | None]] = {"syntax_error": []}

    if not (call_sign := re.match(regex_patterns.CALLSIGN, row_data["call_sign"])):
        err["syntax_error"].append(f"Invalid call-sign({row_data['call_sign']}).")
    else:
        regex_parsed_data["call_sign"] = call_sign.group()

    if not (flt_rule_type := re.match(regex_patterns.FLIGHT_RULE_TYPE, row_data["flt_rule_type"])):
        err["syntax_error"].append(f"Invalid flight rule/type ({row_data['flt_rule_type']}).")
    else:
        regex_parsed_data["flight_rule"] = flt_rule_type.group("flight_rule")
        regex_parsed_data["flight_type"] = flt_rule_type.group("flight_type")

    if not (numbers_type_weak := re.match(regex_patterns.AC_NUMBER_TYPE_WAKE, row_data["numbers_type_weak"])):
        err["syntax_error"].append(f"Invalid numbers/type/weak ({row_data['numbers_type_weak']}).")
    else:
        regex_parsed_data["ac_numbers"] = numbers_type_weak.group("numbers") or "1"
        regex_parsed_data["ac_type"] = numbers_type_weak.group("type")
        regex_parsed_data["ac_weak"] = numbers_type_weak.group("weak")

    if not (
            equp_cpct := re.match(regex_patterns.EQUIPMENTS_CAPACITIES, row_data["equipments_and_capacities"])
    ):
        err["syntax_error"].append(f"Invalid equipments/capacities({row_data['equipments_and_capacities']}).")
    else:
        regex_parsed_data["equipments"] = equp_cpct.group("equipments")
        regex_parsed_data["capacities"] = equp_cpct.group("capacities")

    if not (dep_ad_time := re.match(regex_patterns.DEPARTURE_AD_TIME, row_data["dep_ad_time"])):
        err["syntax_error"].append(f"Invalid departure aerodrome or time ({row_data['dep_ad_time']}).")
    else:
        regex_parsed_data["departure_ad"] = dep_ad_time.groupdict().get("dep_ad")
        regex_parsed_data["eobt"] = dep_ad_time.groupdict().get("eobt")

    if not (dest_teet_alt := re.match(regex_patterns.DEST_AD_TEET_ALTS, row_data["dest_teet_alts"])):
        err["syntax_error"].append(
            f"Invalid destination aerodrome or time or alternates ({row_data['dest_teet_alts']})."
        )
    else:
        regex_parsed_data["destination_ad"] = dest_teet_alt.groupdict().get("dest_ad")
        regex_parsed_data["teet"] = dest_teet_alt.groupdict().get("teet")
        regex_parsed_data["alt_ad_1"] = dest_teet_alt.groupdict().get("alt1")
        regex_parsed_data["alt_ad_2"] = dest_teet_alt.groupdict().get("alt2")

    # Parse Other Information
    other_info: list[str] = row_data["others"].split()
    last_switch_index = 0
    for item in other_info[:]:
        if "/" not in item:
            other_info[last_switch_index] += " " + item
            other_info.remove(item)
        else:
            last_switch_index = other_info.index(item)

    # to create a list of reference points then doing logical-checks on them
    regex_parsed_data["ref_points"] = []

    for item in other_info[:]:
        for key, pattern in OTHER_INFO_SWITCHES.items():
            if item.startswith(f"{key}/"):
                if matched := re.match(pattern, item):
                    regex_parsed_data[key.lower()] = matched.groupdict().get(key)

                    if key == "PBN":
                        regex_parsed_data["pbn_rnav_spc"] = matched.group("rnav_spc")
                        regex_parsed_data["pbn_rnp_spc"] = matched.group("rnp_spc")
                    elif key == "DOF":
                        try:
                            datetime.strptime(regex_parsed_data[key.lower()], "%y%m%d")
                        except ValueError:
                            err["syntax_error"].append(
                                f"DOF({regex_parsed_data[key.lower()]}) is not valid (YYMMDD)."
                            )
                else:
                    err["syntax_error"].append(f"Invalid {item} in ITEM18 (Other information).")
                break
        else:
            err["syntax_error"].append(f"{item} is not valid syntax for ITEM18 (Other information).")

    if regex_parsed_data["departure_ad"] in ("ZZZZ", "AFIL"):
        if "dep" not in regex_parsed_data:
            err["syntax_error"].append(
                "DEP is not defined and missing DEP/ switch in ITEM18 (Other information)."
            )
        elif not re.match(regex_patterns.LOCATION, regex_parsed_data["dep"]):
            err["syntax_error"].append(
                f"DEP/ in ITEM18({regex_parsed_data['dep']}) is not a valid point or coordinate (7 or 11 characters) or bearing-distance."
            )

    if regex_parsed_data["departure_ad"] not in ("ZZZZ", "AFIL"):
        if "dep" in regex_parsed_data:
            err["syntax_error"].append(
                "There must be only one of departure-ad or DEP/ switch in ITEM18 (Other information)."
            )

    if regex_parsed_data["destination_ad"] == "ZZZZ":
        if "dest" not in regex_parsed_data:
            err["syntax_error"].append(
                "DEST is not defined and missing DEST/ switch in ITEM18 (Other information)."
            )
        elif not re.match(regex_patterns.LOCATION, regex_parsed_data["dest"]):
            err["syntax_error"].append(
                f"DEST/ in ITEM18({regex_parsed_data['dest']}) is not a valid point or coordinate (7 or 11 characters) or bearing-distance."
            )

    if regex_parsed_data["destination_ad"] != "ZZZZ":
        if "dest" in regex_parsed_data:
            err["syntax_error"].append(
                "There must be only one of destination-ad or DEST/ switch in ITEM18 (Other information)."
            )

    if regex_parsed_data["alt_ad_1"] == "ZZZZ" or regex_parsed_data["alt_ad_2"] == "ZZZZ":
        if "altn" not in regex_parsed_data:
            err["syntax_error"].append(
                "ALTN is not defined and missing ALTN/ switch in ITEM18 (Other information)."
            )
        elif not re.match(regex_patterns.LOCATION, regex_parsed_data["dest"]):
            err["syntax_error"].append(
                f"ALTN/ in ITEM18({regex_parsed_data['dest']}) is not a valid point or coordinate (7 or 11 characters) or bearing-distance."
            )

    if "dof" not in regex_parsed_data:
        err["syntax_error"].append("Missing DOF/ switch in ITEM18.")

    # Parse Route
    route_regex_parse(row_data, regex_parsed_data, err)

    if err["syntax_error"]:
        errors = {f"{inx}": err for inx, err in enumerate(err["syntax_error"])}
        validation_error = ValidationError(message="Syntax Error", params=errors, code="syntax_error")
    return regex_parsed_data, validation_error
