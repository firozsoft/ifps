import re

"""PLEASE READ PANS-ATM APPENDIX 2
The instructions for the completion of the flight plan form is included in PANS-ATM Appendix 2
the comments in this module below are also derived from that document but these comments are mostly
limited to the code written in this mudole and not the hole logic to be developed.

This mudole contains RegexPatterns matching the items of flight plan as prescribed in PANS-ATM Appendix 2
"""


# ? ITEM 7: AIRCRAFT IDENTIFICATION (MAXIMUM 7 CHARACTERS)
# not exceeding 7 alphanumeric characters
CALLSIGN = r"\b[A-Z\d]{2,7}\b"


# ? ITEM 8: FLIGHT RULES AND TYPE OF FLIGHT (ONE OR TWO CHARACTERS)
# * Flight rules
# I  if it is intended that the entire flight will be operated under the IFR
# V  if it is intended that the entire flight will be operated under the VFR
# Y  if the flight initially will be operated under the IFR, followed by one or more subsequent changes of flight rules or
# Z  if the flight initially will be operated under the VFR, followed by one or more subsequent changes of flight rules
# TODO: Specify in Item 15 the point or points at which a change of flight rules is planned.
# * Type of flight
# S  if scheduled air service
# N  if non-scheduled air transport operation
# G  if general aviation
# M  if military
# X  if other than any of the defined categories above.
# TODO: Specify status of a flight following the indicator STS in Item 18, or when necessary to denote other reasons for specific handling by ATS, indicate the reason following the indicator RMK in Item 18.
FLIGHT_RULE_TYPE = r"\b(?P<flight_rule>[I,V,Y,Z])(?P<flight_type>[S,N,G,M,X]?)\b"


# ? ITEM 9: NUMBER AND TYPE OF AIRCRAFT AND WAKE TURBULENCE CATEGORY
# * Number of aircraft (1 or 2 characters)
# the number of aircraft, if more than one else nothing -> as regex eq {0,2}
# * Type of aircraft (2 to 4 characters)
# TODO: The appropriate designator as specified in Doc 8643, Aircraft Type Designators, or if no such designator has been assigned, or in case of formation flights comprising more than one type, ZZZZ, and SPECIFY in Item 18, the (numbers and) type(s) of aircraft preceded by TYP/
# * Wake turbulence category (1 character)
AC_NUMBER_TYPE_WAKE = r"\b(?P<numbers>\d{0,2})(?P<type>[A-Z\d]{2,4})\/(?P<weak>[H,M,L,J])\b"


# ? ITEM 10: EQUIPMENT AND CAPABILITIES
# TODO: create named-group in regex pattern so to match "standard", "CPDLC", "SATVOICE", "SSR MODE S", "ADS-B,C"
# * Radiocommunication, navigation and approach aid equipment and capabilities
# N  if no COM/NAV/approach aid equipment for the route to be flown is carried, or the equipment is unserviceable
# S  if standard COM/NAV/approach aid equipment for the route to be flown is carried and serviceable
# OR One or More of the followings
# A  GBAS landing system
# B  LPV (APV with SBAS)
# C  LORAN C
# D  DME
# E1  FMC WPR ACARS
# E2  D-FIS ACARS
# E3  PDC ACARS
# F  ADF
# G  GNSS. If any portion of the flight is planned to be conducted under IFR, it refers to GNSS receivers that comply with the requirements of Annex 10, Volume I
# H  HF RTF
# I  Inertial Navigation
# J1  CPDLC ATN VDL Mode 2
# J2  CPDLC FANS 1/A HFDL
# J3  CPDLC FANS 1/A VDL Mode A
# J4  CPDLC FANS 1/A VDL Mode 2
# J5  CPDLC FANS 1/A SATCOM (INMARSAT)
# J6  CPDLC FANS 1/A SATCOM (MTSAT)
# J7  CPDLC FANS 1/A SATCOM (Iridium)
# K  MLS
# L  ILS
# M1  ATC SATVOICE (INMARSAT)
# M2  ATC SATVOICE (MTSAT)
# M3  ATC SATVOICE (Iridium)
# O  VOR
# P1  CPDLC RCP 400 (See Note 7)
# P2  CPDLC RCP 240 (See Note 7)
# P3  SATVOICE RCP 400 (See Note 7)
# P4-P9  Reserved for RCP
# R  PBN approved (See Note 4)
# T  TACAN
# U  UHF RTF
# V  VHF RTF
# W  RVSM approved
# X  MNPS approved
# Y  VHF with 8.33 kHz channel spacing capability
# Z  Other equipment carried or other capabilities

# * Surveillance equipment and capabilities
# N if no surveillance equipment for the route to be flown is carried, or the equipment is unserviceable or
# one or more of the following descriptors, to a maximum of 20 characters, to describe the serviceable surveillance equipment and/or capabilities on board

# SSR Modes A and C
#   A  Transponder — Mode A (4 digits — 4 096 codes)
#   C  Transponder — Mode A (4 digits — 4 096 codes) and Mode C

# SSR Mode S
#   E  Transponder — Mode S, including aircraft identification, pressure-altitude and extended squitter (ADS-B) capability
#   H  Transponder — Mode S, including aircraft identification, pressure-altitude and enhanced surveillance capability
#   I  Transponder — Mode S, including aircraft identification, but no pressure-altitude capability
#   L  Transponder — Mode S, including aircraft identification, pressure-altitude, extended squitter (ADS-B) and enhanced surveillance capability
#   P  Transponder — Mode S, including pressure-altitude, but no aircraft identification capability
#   S  Transponder — Mode S, including both pressure altitude and aircraft identification capability
#   X  Transponder — Mode S, with neither aircraft identification nor pressure-altitude capability

# ADS-B
#   B1  ADS-B with dedicated 1 090 MHz ADS-B “out” capability
#   B2  ADS-B with dedicated 1 090 MHz ADS-B “out” and “in” capability
#   U1  ADS-B “out” capability using UAT
#   U2  ADS-B “out” and “in” capability using UAT
#   V1  ADS-B “out” capability using VDL Mode 4
#   V2  ADS-B “out” and “in” capability using VDL Mode 4

# ADS-C
#   D1  ADS-C with FANS 1/A capabilities
#   G1  ADS-C with ATN capabilities

# * Example:  ADE3RV/HB2U2V2G1

# Note 2.— Additional surveillance equipment or capabilities will be listed in Item 18 following the indicator SUR/, as required by the appropriate ATS authority
EQUIPMENTS_CAPACITIES = r"\b(?P<equipments>(N|S|A|B|C|D|E1|E2|E3|F|G|H|I|J[1-7]|K|L|M[1-3]|O|P[1-9]|R|T|U|V|W|X|Y|Z)+)\/(?P<capacities>(A|C|E|H|I|L|P|S|X|B1|B2|U1|U2|V1|V2|D1|G1){0,20})\b"


# ? ITEM 13: DEPARTURE AERODROME AND TIME (8 CHARACTERS)
# Insert all clock times in 4 figures UTC
# Insert all estimated elapsed times in 4 figures (hours and minutes)
# TODO: ZZZZ/AFIL and SPECIFY, in Item 18, the name and location of the aerodrome preceded by DEP/
DEPARTURE_AD_TIME = r"\b((?P<dep_ad>[A-Z]{4})|AFIL|ZZZZ)(?P<eobt>((0|1)[0-9]|2[0-3])[0-5][0-9])\b"


# ? ITEM 15: ROUTE
# * INSERT the first cruising speed as in (a) and the first cruising level as in (b), without a space between them.
# * THEN, INSERT the route description as in (c).
# //
# * (a) Cruising speed (maximum 5 characters)
# Kilometres per hour, expressed as K followed by 4 figures (e.g. K0830), or
# Knots, expressed as N followed by 4 figures (e.g. N0485), or
# True Mach number, when so prescribed by the appropriate ATS authority, to the nearest hundredth of unit Mach, expressed as M followed by 3 figures (e.g. M082).
SPEED = r"\b(?P<speed>(K(0|1)\d{3})|(N0\d{3})|(M(0\d\d|10\d)))\b"

# * (b) Cruising level (maximum 5 characters)
# Flight level, expressed as F followed by 3 figures (e.g. F085; F330), or
# Standard metric level in tens of metres, expressed as S followed by 4 figures (e.g. S1130), or
# Altitude in hundreds of feet, expressed as A followed by 3 figures (e.g. A045; A100), or
# Altitude in tens of metres, expressed as M followed by 4 figures (e.g. M0840), or
# for uncontrolled VFR flights, the letters VFR.
LEVEL = r"\b(?P<level>(F\d\d[0,5])|(S\d{3}0)|(A\d\d[0,5])|(M\d{4})|(VFR))\b"

SPEED_LEVEL = r"\b{0}{1}\b".format(SPEED.replace("\\b", ""), LEVEL.replace("\\b", ""))


# * (c) Route (including changes of speed, level and/or flight rules)
# Route | (DCT Point Route) -> then:
# each point at which either a change of speed and/or level is planned to commence, or
# a change of ATS route, and/or
# a change of flight rules is planned
# FOLLOWED IN EACH CASE
# by the designator of the next ATS route segment, even if the same as the previous one, or
# by DCT, if the flight to the next point will be outside a designated route,
# unless both points are defined by geographical coordinates or by bearing and distance.
# ? USE ONLY the conventions in (1) to (5) below and SEPARATE each sub-item by a space.

# ? Degrees only (7 characters)
COR_DEGREES = r"\b(?P<degrees>(([0-8]\d)|90)(N|S)((0\d\d)|(1[0-7]\d)|180)(E|W))\b"

# ? Degrees and minutes (11 characters)
COR_DEG_MINS = r"\b(?P<deg_min>(([0-8]\d)|90)[0-5]\d(N|S)((0\d\d)|(1[0-7]\d)|180)[0-5]\d(E|W))\b"

# ? The coded designator (2 to 5 characters) assigned to the point (e.g. LN, MAY, HADDY)
POINT = r"\b(?P<point>([A-Z]{2,5})(?<!DCT|IFR|VFR))\b"

# ? Bearing and distance from a reference point (point which has a designator)
BEARING_DIST = (
    r"\b(?P<bearing_dist>(?P<ref_point>([A-Z]{2,5})(?<!DCT|IFR|VFR))(([0-2]\d\d)|(3[0-5]\d))[0-2]\d\d)\b"
)

# ? Points that don't have assigned indicator - referred to as special point
LOCATION = r"\b(?P<location>({0})|({1})|({2}))\b".format(
    BEARING_DIST.replace("\\b", ""), COR_DEGREES.replace("\\b", ""), COR_DEG_MINS.replace("\\b", "")
)

# * 1- ATS route (2 to 7 characters) ! 7 characters only for SID/STAR
ROUTE = r"\b(?P<route>[A-Z]{1,3}\d{1,3})\b"
SID_STAR = r"\b(?P<sid_star>({0})\d[A-Z])\b".format(POINT.replace("\\b", ""))

# * 2- Significant point (2 to 11 characters)
# ? All point matching those regexes above
SIG_POINT = r"\b(?P<sig_point>{0}|{1})\b".format(POINT.replace("\\b", ""), LOCATION.replace("\\b", ""))

# * 3- Change of speed or level (maximum 21 characters)
# Examples:   LN/N0284A045, MAY/N0305Fl80, HADDY/N0420F330, 4602N07805W/N0500F350, 46N078W/M082F330, DUB180040/N0350M0840
CHANGE_SPEED_LEVEL = r"\b(?P<change_speed_level>{0}\/{1})\b".format(
    SIG_POINT.replace("\\b", ""), SPEED_LEVEL.replace("\\b", "")
)

# * 4- Change of flight rules (maximum 3 characters)
# (Point (as in 2- above) Or ChangeOfSpeedLevel(as in 3- above)) + 1 space + IFR/VFR
CHANGE_FLT_RULE = r"\b(?P<change_flt_rule>({0}(\/{1})?)\s+(VFR|IFR))\b".format(
    SIG_POINT.replace("\\b", ""), SPEED_LEVEL.replace("\\b", "")
)

# * 5- Cruise climb (maximum 28 characters)
# letter C followed by an oblique stroke (/), a point as in 2 above followed by an oblique stroke, the speed, lower level, upper level or the word PLUS
# C/SIG_POINT/SPEED_LEVEL(LEVEL|PLUS)
# Examples:  C/48N050W/M082F290F350, C/48N050W/M082F290PLUS, C/LN011032/M220F580F620
CRUISE_CLIMB = r"\b(?P<cruiseclimb>C\/{0}\/({1})({2}|PLUS))\b".format(
    SIG_POINT.replace("\\b", ""),
    SPEED_LEVEL.replace("\\b", ""),
    LEVEL.replace("\\b", "").replace("level", "top_level"),
)

# ? ITEM 16: DESTINATION AERODROME AND TOTAL ESTIMATED ELAPSED TIME, DESTINATION ALTERNATE AERODROME(S)
# * Destination aerodrome and total estimated elapsed time (8 characters)
# the ICAO four-letter location indicator, or
# ZZZZ and in Item 18 the name and location of the aerodrome, preceded by DEST/
# then witout a space the total estimated elapsed time.
# * Destination alternate aerodrome(s)
# the ICAO four-letter location indicator(s) of not more than two destination alternate aerodromes, or
# ZZZZ and SPECIFY in Item 18 the name and location of the destination alternate aerodrome(s), preceded by ALTN/
DEST_AD_TEET_ALTS = r"\b(?P<dest_teet_alt>(?P<dest_ad>[A-Z]{4})(?P<teet>\d{4})(\s(?P<alt1>[A-Z]{4}))?(\s(?P<alt2>[A-Z]{4}))?)\b"

# ? ITEM 18: OTHER INFORMATION
OTHER_INFO_SWITCHES = [
    "STS",
    "PBN",
    "NAV",
    "COM",
    "DAT",
    "SUR",
    "DOF",
    "REG",
    "EET",
    "SEL",
    "TYP",
    "CODE",
    "DLE",
    "OPR",
    "ORGN",
    "PER",
    "DEP",
    "ALTN",
    "RALT",
    "TALT",
    "RIF",
    "RMK",
]


def _other_switches(switch: str) -> list[str]:
    res = OTHER_INFO_SWITCHES[:]
    # NOTE: list.remove works inplace (it returns None)
    res.remove(switch)
    return res


RNAV_SPC = r"\b(?P<RNAV_SPC>(A1|B[1-6]|C[1-4]|D[1-4]){1,4})\b"

RNP_SPC = r"\b(?P<RNP_SPC>(L1|O[1-4]|S[1-2]|T[1-2]){1,4})\b"

STS = (
    r"\bSTS\/(?P<STS>(ALTRV|ATFMX|FFR|FLTCK|HAZMAT|HEAD|HOSP|HUM|MARSA|MEDEVAC|NONRVSM|SAR|STATE)+)"
    + r"(?!("
    + r"|".join(_other_switches("STS"))
    + r"))\b"
)

PBN = (
    r"\bPBN\/(?P<PBN>({0})({1}))".format(RNAV_SPC.replace("\\b", ""), RNP_SPC.replace("\\b", ""))
    + r"(?!("
    + r"|".join(_other_switches("PBN"))
    + r"))\b"
)

NAV = (
    r"\bNAV\/(?P<NAV>(?P<nav_key>SBAS|GBAS|ABAS|DGNSS|RTK|WARTK|PPP)(\s(?P=nav_key))?)"
    + r"(?!("
    + r"|".join(_other_switches("NAV"))
    + r"))\b"
)

COM = r"\bCOM\/(?P<COM>[A-Z\d]+)" + r"(?!(" + r"|".join(_other_switches("COM")) + r"))\b"

DAT = r"\bDAT\/(?P<DAT>[A-Z\d]+)" + r"(?!(" + r"|".join(_other_switches("DAT")) + r"))\b"

SUR = r"\bSUR\/(?P<SUR>(RSP\d{3})(\sRSP\d{3})?)" + r"(?!(" + r"|".join(_other_switches("SUR")) + r"))\b"

DOF = (
    r"\bDOF\/(?P<DOF>\d{2}((0\d)|1[0-2])(([0-2]\d)|3[0-1]))"
    + r"(?!("
    + r"|".join(_other_switches("DOF"))
    + r"))\b"
)

REG = r"\bREG\/(?P<REG>[A-Z\d]+)" + r"(?!(" + r"|".join(_other_switches("REG")) + r"))\b"

EET = (
    r"\bEET\/(?P<EET>([A-Z]{4}\d{4})(\s[A-Z]{4}\d{4})*)"
    + r"(?!("
    + r"|".join(_other_switches("EET"))
    + r"))\b"
)

SEL = r"\bSEL\/(?P<SEL>[A-Z]+)" + r"(?!(" + r"|".join(_other_switches("SEL")) + r"))\b"

TYP = r"\bTYP\/(?P<TYP>(\d)?[A-Z\d]+)" + r"(?!(" + r"|".join(_other_switches("TYP")) + r"))\b"

CODE = r"\bCODE\/(?P<CODE>(F[A-F\d]{5})(?<!F00000))" + r"(?!(" + r"|".join(_other_switches("CODE")) + r"))\b"

DLE = (
    r"\bDLE\/(?P<DLE>{0}\d\d[0-5]\d)".format(POINT.replace("\\b", ""))
    + r"(?!("
    + r"|".join(_other_switches("DLE"))
    + r"))\b"
)

OPR = r"\bOPR\/(?P<OPR>[A-Z\d]+)" + r"(?!(" + r"|".join(_other_switches("OPR")) + r"))\b"

ORGN = r"\bORGN\/(?P<ORGN>[A-Z]{8})" + r"(?!(" + r"|".join(_other_switches("ORGN")) + r"))\b"

PER = r"\bPER\/(?P<PER>[A-Z])" + r"(?!(" + r"|".join(_other_switches("PER")) + r"))\b"

DEP = (
    r"\bDEP\/(?P<DEP>((?P<aerodrome>[A-Z]{{4}})|({0})|({1})|({2}))".format(
        COR_DEG_MINS.replace("\\b", ""),
        BEARING_DIST.replace("\\b", ""),
        POINT.replace("\\b", ""),
    )
    + r"(?!("
    + r"|".join(_other_switches("DEP"))
    + r")))\b"
)

ALTN = DEP.replace(r"DEP\/", r"ALTN\/", 2)

RALT = DEP.replace(r"DEP\/", r"RALT\/", 2)

TALT = DEP.replace(r"DEP\/", r"TALT\/", 2)

ROUTESCHEME_PATH = r"(\b[A-Z]{2,5}\d[A-Z]\b)?\s(\b[A-Z]{2,5}\b)\s(\b[A-Z]{1,3}\d{1,3}\b)\s((\b[A-Z]{2,5}\b)?\s(\b[A-Z]{1,3}\d{1,3}\b)?)+\s(\b[A-Z]{2,5}\b)\s(\b[A-Z]{2,5}\d[A-Z]\b)?"

RIF = (
    r"\b(?P<RIF>{0}\s(?P<revised_dest_ad>[A-Z]{{4}}))\b".format(ROUTESCHEME_PATH.replace("\\b", ""))
    + r"(?!("
    + r"|".join(_other_switches("RIF"))
    + r"))\b"
)

RMK = r"\bRMK\/(?P<RMK>\w+)" + r"(?!(" + r"|".join(_other_switches("RMK")) + r"))\b"

# fmt: off
flight_plan_route_pattern = (
    r"{speed_level} ({SID_STAR}|DCT {point} {route}) "
    r"(({point}|{CHANGE_SPEED_LEVEL}|{CHANGE_FLT_RULE}|{route}) )+"
    r" ({SID_STAR}|{point})$"
).format(
    speed_level=SPEED_LEVEL.replace("\\b", ""),
    SID_STAR=SID_STAR.replace("\\b", ""),
    route=ROUTE.replace("\\b", ""),
    point=LOCATION.replace("\\b", ""),
    CHANGE_SPEED_LEVEL=CHANGE_SPEED_LEVEL.replace("\\b", ""),
    CHANGE_FLT_RULE=CHANGE_FLT_RULE.replace("\\b", ""),
)


fpl_route_pattern = re.sub(r"\?P<\w+>", "", flight_plan_route_pattern)
fpl_route_pattern = r"((K(0|1)\d{3})|(N0\d{3})|(M(0\d\d|10\d)))((F\d\d[0,5])|(S\d{3}0)|(A\d\d[0,5])|(M\d{4})) ((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))\d[A-Z])|DCT (((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2]\d\d)|(3[0-5]\d))[0-2]\d\d))|(((([0-8]\d)|90)(N|S)((0\d\d)|(1[0-7]\d)|180)(E|W)))|(((([0-8]\d)|90)[0-5]\d(N|S)((0\d\d)|(1[0-7]\d)|180)[0-5]\d(E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR)))) ([A-Z]{1,3}\d{1,3})) (((((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2]\d\d)|(3[0-5]\d))[0-2]\d\d))|(((([0-8]\d)|90)(N|S)((0\d\d)|(1[0-7]\d)|180)(E|W)))|(((([0-8]\d)|90)[0-5]\d(N|S)((0\d\d)|(1[0-7]\d)|180)[0-5]\d(E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR))))|(((((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2]\d\d)|(3[0-5]\d))[0-2]\d\d))|(((([0-8]\d)|90)(N|S)((0\d\d)|(1[0-7]\d)|180)(E|W)))|(((([0-8]\d)|90)[0-5]\d(N|S)((0\d\d)|(1[0-7]\d)|180)[0-5]\d(E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR)))))\/((K(0|1)\d{3})|(N0\d{3})|(M(0\d\d|10\d)))((F\d\d[0,5])|(S\d{3}0)|(A\d\d[0,5])|(M\d{4})))|(((((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2]\d\d)|(3[0-5]\d))[0-2]\d\d))|(((([0-8]\d)|90)(N|S)((0\d\d)|(1[0-7]\d)|180)(E|W)))|(((([0-8]\d)|90)[0-5]\d(N|S)((0\d\d)|(1[0-7]\d)|180)[0-5]\d(E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR))))|((((((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2]\d\d)|(3[0-5]\d))[0-2]\d\d))|(((([0-8]\d)|90)(N|S)((0\d\d)|(1[0-7]\d)|180)(E|W)))|(((([0-8]\d)|90)[0-5]\d(N|S)((0\d\d)|(1[0-7]\d)|180)[0-5]\d(E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR)))))\/((K(0|1)\d{3})|(N0\d{3})|(M(0\d\d|10\d)))((F\d\d[0,5])|(S\d{3}0)|(A\d\d[0,5])|(M\d{4})))))\s(VFR|IFR))|([A-Z]{1,3}\d{1,3})) )+ ((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))\d[A-Z])|(((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2]\d\d)|(3[0-5]\d))[0-2]\d\d))|(((([0-8]\d)|90)(N|S)((0\d\d)|(1[0-7]\d)|180)(E|W)))|(((([0-8]\d)|90)[0-5]\d(N|S)((0\d\d)|(1[0-7]\d)|180)[0-5]\d(E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR)))))$"
