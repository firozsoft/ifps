"""PLEASE READ PANS-ATM APPENDIX 2.

The instructions for the completion of the flight plan form is included in PANS-ATM Appendix 2
the comments in this module below are also derived from that document but these comments are mostly
limited to the code written in this mudole and not the hole logic to be developed.

This mudole contains RegexPatterns matching the items of flight plan as prescribed in PANS-ATM Appendix 2
"""

# The r"^(?![IJXQ])(?P<aerodrome>[A-Z]{4})$" pattern is shorter but due to pydantic problem is not usable
AERODROME = r"^(?P<aerodrome>[A-HK-WYZ][A-Z]{3})$"
FIR = r"^(?P<fir>[A-HK-WYZ][A-Z]{3})$"
AFTN_ADDRESS = r"^[A-HK-WYZ][A-Z]{8}$"

# ? ITEM 7: AIRCRAFT IDENTIFICATION (MAXIMUM 7 CHARACTERS)
# not exceeding 7 alphanumeric characters
AIRCRAFT_IDENTIFICATION = r"^(?P<aircraft_identification>[A-Z\d]{2,7})$"


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
FLIGHT_RULE = r"^(?P<flight_rule>[IVYZ])$"
TYPE_OF_FLIGHT = r"^(?P<type_of_flight>[SNGMX]?)$"
FLIGHT_RULE_AND_TYPE = r"^(?P<flight_rule>[IVYZ])(?P<type_of_flight>[SNGMX]?)$"


# ? ITEM 9: NUMBER AND TYPE OF AIRCRAFT AND WAKE TURBULENCE CATEGORY
# * Number of aircraft (1 or 2 characters)
# the number of aircraft, if more than one else nothing -> as regex eq {0,2}
# * Type of aircraft (2 to 4 characters)
# TODO: The appropriate designator as specified in Doc 8643, Aircraft Type Designators, or if no such designator has been assigned, or in case of formation flights comprising more than one type, ZZZZ, and SPECIFY in Item 18, the (numbers and) type(s) of aircraft preceded by TYP/
# * Wake turbulence category (1 character)
TYPE_OF_AIRCRAFT = r"^(?P<type>[A-Z\d]{2,4})$"
WAKETURBULENCE_CATEGORY = r"^(?P<weakturbulence_category>[HMLJ])$"
AC_NUMBER_TYPE_WAKE = r"^(?P<number_of_aircraft>\d{0,2})(?P<type_of_aircraft>[A-Z\d]{2,4})\/(?P<weakturbulence_category>[HMLJ])$"


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
EQUIPMENTS = r"^(?P<equipments>N|(?:S|A|B|C|D|E1|E2|E3|F|G|H|I|J[1-7]|K|L|M[1-3]|O|P[1-9]|R|T|U|V|W|X|Y|Z)+)$"
CAPABILITIES = r"^(?P<capabilities>N|(?:(?:A|C|E|H|I|L|P|S|X)?(B1|B2)?(U1|U2)?(V1|V2)?(D1|G1)?){1,20})$"

EQUIPMENTS_CAPABILITIES = r"^{equipments}\/{capabilities}$".format(
    equipments=EQUIPMENTS.replace(r"^", "").replace(r"$", ""),
    capabilities=CAPABILITIES.replace(r"^", "").replace(r"$", ""),
)


# ? ITEM 13: DEPARTURE AERODROME AND TIME (8 CHARACTERS)
# Insert all clock times in 4 figures UTC
# Insert all estimated elapsed times in 4 figures (hours and minutes)
# TODO: ZZZZ/AFIL and SPECIFY, in Item 18, the name and location of the aerodrome preceded by DEP/
DEPARTURE_AD_TIME = r"^(?:{ad}|AFIL|ZZZZ)(?P<eobt>(?:[01]\d|2[0-3])[0-5]\d)$".format(
    ad=AERODROME.replace(r"^", "").replace(r"$", "").replace("<aerodrome>", "<departure_ad>"),
)


# ? ITEM 15: ROUTE
# * INSERT the first cruising speed as in (a) and the first cruising level as in (b), without a space between them.
# * THEN, INSERT the route description as in (c).
# //
# * (a) Cruising speed (maximum 5 characters)
# Kilometres per hour, expressed as K followed by 4 figures (e.g. K0830), or
# Knots, expressed as N followed by 4 figures (e.g. N0485), or
# True Mach number, when so prescribed by the appropriate ATS authority, to the nearest hundredth of unit Mach, expressed as M followed by 3 figures (e.g. M082).
SPEED = r"^(?P<speed>K(?:0|1)\d{3}|N0\d{3}|M(?:0\d\d|10\d))$"

# * (b) Cruising level (maximum 5 characters)
# Flight level, expressed as F followed by 3 figures (e.g. F085; F330), or
# Standard metric level in tens of metres, expressed as S followed by 4 figures (e.g. S1130), or
# Altitude in hundreds of feet, expressed as A followed by 3 figures (e.g. A045; A100), or
# Altitude in tens of metres, expressed as M followed by 4 figures (e.g. M0840), or
# for uncontrolled VFR flights, the letters VFR.
LEVEL = r"^(?P<level>F\d\d[0,5]|S\d{3}0|A\d\d[0,5]|M\d{4}|VFR)$"

SPEED_LEVEL = r"^{spd}{lvl}$".format(
    spd=SPEED.replace(r"^", "").replace(r"$", ""),
    lvl=LEVEL.replace(r"^", "").replace(r"$", ""),
)


# * (c) Route (including changes of speed, level and/or flight rules)
# Route | (DCT Point Route) -> then:
# each point at which either a change of speed and/or level is planned to commence, or
# a change of ATS route, and/or
# a change of flight rules is planned
# FOLLOWED IN EACH CASE
# by the designator of the next ATS route segment, even if the same as the previous one, or
# by DCT, if the flight to the next point will be outside a designated route,
# unless both points are defined by geographical coordinate or by bearing and distance.
# ? USE ONLY the conventions in (1) to (5) below and SEPARATE each sub-item by a space.

# ? Degrees only (7 characters) or degrees and minutes (11 characters)
COORDINATE = r"^(?P<coordinate>(?:[0-8]\d|90)(?:[0-5]\d)?[NS](?:0\d\d|1[0-7]\d|180)(?:[0-5]\d)?[EW])$"

# ? The coded designator (2 to 5 characters) assigned to the point (e.g. LN, MAY, HADDY)
POINT = r"^(?!(?:DCT|IFR|VFR)$)(?P<point>[A-Z]{2,5})$"

# ? Bearing and distance from a reference point (point which has a designator)
BEARING_DIST = r"^(?P<bearing_dist>{pnt}(?:[0-2]\d\d|3[0-5]\d)[0-3]\d\d)$".format(
    pnt=POINT.replace(r"^", "").replace(r"$", "").replace("<point>", "<ref_point>"),
)

# ? Points that don't have assigned indicator - referred to as special point
LOCATION = r"^(?P<location>{brd}|{coordinate})$".format(
    brd=BEARING_DIST.replace(r"^", "").replace(r"$", ""),
    coordinate=COORDINATE.replace(r"^", "").replace(r"$", ""),
)

# * 1- ATS route (2 to 7 characters) ! 7 characters only for SID/STAR
ROUTE = r"^(?P<route>[A-Z]{1,3}\d{1,3})$"
SID_STAR = r"^(?P<sid_star>{pnt}\d[A-Z])$".format(pnt=POINT.replace(r"^", "").replace(r"$", ""))
SID_POINT = r"^(?P<sid>([A-Z]{3,5})\d[A-Z]) \2$"
POINT_STAR = r"^([A-Z]{3,5}) (?P<star>\1\d[A-Z])$"

# * 2- Significant point (2 to 11 characters)
# ? All point matching those regexes above
SIG_POINT = r"^(?P<sig_point>{pnt}|{loc})$".format(
    pnt=POINT.replace(r"^", "").replace(r"$", ""),
    loc=LOCATION.replace(r"^", "").replace(r"$", ""),
)

# * 3- Change of speed or level (maximum 21 characters)
# Examples:   LN/N0284A045, MAY/N0305Fl80, HADDY/N0420F330, 4602N07805W/N0500F350, 46N078W/M082F330, DUB180040/N0350M0840
CHANGE_SPEED_LEVEL = r"^(?P<change_speed_level>{sigp}\/{splvl})$".format(
    sigp=SIG_POINT.replace(r"^", "").replace(r"$", ""),
    splvl=SPEED_LEVEL.replace(r"^", "").replace(r"$", ""),
)

# * 4- Change of flight rules (maximum 3 characters)
# (Point (as in 2- above) Or ChangeOfSpeedLevel(as in 3- above)) + 1 space + IFR/VFR
CHANGE_FLT_RULE = r"^(?P<change_flt_rule>{sigp}(?:\/{splvl})?\s(?:VFR|IFR))$".format(
    sigp=SIG_POINT.replace(r"^", "").replace(r"$", ""),
    splvl=SPEED_LEVEL.replace(r"^", "").replace(r"$", ""),
)

# * 5- Cruise climb (maximum 28 characters)
# letter C followed by an oblique stroke (/), a point as in 2 above followed by an oblique stroke,
# the speed, lower level, upper level or the word PLUS C/SIG_POINT/SPEED_LEVEL(LEVEL|PLUS)
# Examples:  C/48N050W/M082F290F350, C/48N050W/M082F290PLUS, C/LN011032/M220F580F620
CRUISE_CLIMB = r"^(?P<cruise_climb>C\/{sigp}\/{splvl}(?:{lvl}|PLUS))$".format(
    sigp=SIG_POINT.replace(r"^", "").replace(r"$", ""),
    splvl=SPEED_LEVEL.replace(r"^", "").replace(r"$", ""),
    lvl=LEVEL.replace(r"^", "").replace(r"$", "").replace("level", "top_level"),
)

# ? ITEM 16: DESTINATION AERODROME AND TOTAL ESTIMATED ELAPSED TIME, DESTINATION ALTERNATE AERODROME(S)
# * Destination aerodrome and total estimated elapsed time (8 characters)
# the ICAO four-letter location indicator, or
# ZZZZ and in Item 18 the name and location of the aerodrome, preceded by DEST/
# then witout a space the total estimated elapsed time.
# * Destination alternate aerodrome(s)
# the ICAO four-letter location indicator(s) of not more than two destination alternate aerodromes, or
# ZZZZ and SPECIFY in Item 18 the name and location of the destination alternate aerodrome(s), preceded by ALTN/
TEET = r"^(?P<teet>\d\d[0-5]\d)$"
DEST_AD_TEET_ALTS = r"^(?P<dest_teet_alt>{ad0}(?P<teet>\d\d[0-5]\d)\s{ad1}(?:\s{ad2})?)$".format(
    ad0=AERODROME.replace(r"^", "").replace(r"$", "").replace("<aerodrome>", "<destination_ad>"),
    ad1=AERODROME.replace(r"^", "").replace(r"$", "").replace("<aerodrome>", "<alt_ad_1>"),
    ad2=AERODROME.replace(r"^", "").replace(r"$", "").replace("<aerodrome>", "<alt_ad_2>"),
)

RNAV_SPC = r"^(?P<rnav_specification>(?:A1|B[1-6]|C[1-4]|D[1-4]){1,4})$"

RNP_SPC = r"^(?P<rnp_specification>(?:L1|O[1-4]|S[1-2]|T[1-2]){1,4})$"

STS = (
    r"^STS\/(?P<STS>(?:(?:ALTRV|ATFMX|FFR|FLTCK|HAZMAT|HEAD|HOSP|HUM|MARSA|MEDEVAC|NONRVSM|SAR|STATE)\s?)+)$"
)

PBN = r"^PBN\/(?P<PBN>{rnv}{rnp})$".format(
    rnv=RNAV_SPC.replace(r"^", "").replace(r"$", ""),
    rnp=RNP_SPC.replace(r"^", "").replace(r"$", ""),
)

NAV = r"^NAV\/(?P<NAV>(?:(?:SBAS|GBAS|ABAS|DGNSS|RTK|WARTK|PPP|RNP\d)\s?)+)$"

COM = r"^COM\/(?P<COM>[A-Z\d\s]+)$"

DAT = r"^DAT\/(?P<DAT>[A-Z\d\s]+)$"

SUR = r"^SUR\/(?P<SUR>[A-Z\d\s]+)$"

DOF = r"^DOF\/(?P<DOF>\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))$"

REG = r"^REG\/(?P<REG>[A-Z\d]+)$"

EET = r"^EET\/(?P<EET>[A-HK-WYZ][A-Z]{3}\d{2}[0-5]\d(?:\s[A-HK-WYZ][A-Z]{3}\d{2}[0-5]\d)*)$"

SEL = r"^SEL\/(?P<SEL>[A-Z]+)$"

TYP = r"^TYP\/(?P<TYP>(?:[2-9]\d?)?[A-Z\d]{2,4}(?:\s(?:[2-9]\d?)?[A-Z\d]{2,4})?)$"

CODE = r"^CODE\/(?P<CODE>[0-9A-F]{6})$"

DLE = r"^DLE\/(?P<DLE>{point}\d\d[0-5]\d)$".format(point=POINT.replace(r"^", "").replace(r"$", ""))

OPR = r"^OPR\/(?P<OPR>[A-Z\d]+)$"

ORGN = r"^ORGN\/(?P<ORGN>[A-Z]{8})$"

PER = r"^PER\/(?P<PER>[A-Z])$"

DEP = r"^DEP\/(?P<DEP>{ad}|{sigp})$".format(
    ad=AERODROME.replace(r"^", "").replace(r"$", ""),
    sigp=SIG_POINT.replace(r"^", "").replace(r"$", ""),
)

DEST = DEP.replace("DEP", "DEST", 2)

ALTN = DEP.replace("DEP", "ALTN", 2)

RALT = DEP.replace("DEP", "RALT", 2)

TALT = DEP.replace("DEP", "TALT", 2)

# TODO: RIF data needs to be parsed just like route item
# RIF/ _> The route details to the revised destination aerodrome,
# followed by the ICAO four-letter location indicator of the aerodrome.
# The revised route is subject to reclearance in flight.
#   Examples: 1- RIF/DTA HEC KLAX  2- RIF/ESP G94 CLA YPPH

RIF = r"RIF\/(?P<RIF>\w+\s(?P<revised_dest_ad>[A-Z]{4}))$"

RMK = r"^RMK\/(?P<RMK>[\w\s]+)$"

OTHER_INFO_SWITCHES_MAPPING = {
    "STS": STS,
    "PBN": PBN,
    "NAV": NAV,
    "COM": COM,
    "DAT": DAT,
    "SUR": SUR,
    "DOF": DOF,
    "REG": REG,
    "EET": EET,
    "SEL": SEL,
    "TYP": TYP,
    "CODE": CODE,
    "DLE": DLE,
    "OPR": OPR,
    "ORGN": ORGN,
    "PER": PER,
    "DEP": DEP,
    "DEST": DEST,
    "ALTN": ALTN,
    "RALT": RALT,
    "TALT": TALT,
    "RIF": RIF,
    "RMK": RMK,
}
