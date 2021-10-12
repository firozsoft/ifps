REG_PATTERNS = (
    r"(?P<call_sign>[A-Z\d]{2,7})"
    r"(?P<flt_rule_and_type>(?P<flt_rule>[I,V,Y,Z])(?P<flt_type>[S,N,G,M,X]?))"
    r"(?P<ac_num_an_type_and_wake>(?P<number_of_ac>[\d]{0,2})(?P<ac_type>[A-Z\d]{2,4})\/(?P<ac_weak>[H,M,L,J]))"
    r"(?P<equipments_and_capacities>(?P<equipments>(N|S|A|B|C|D|E1|E2|E3|F|G|H|I|J1|J2|J3|J4|J5|J6|J7|K|L|M1|M2|M3|O|P1|P2|P3|P4|P5|P6|P7|P8|P9|R|T|U|V|W|X|Y|Z)+)\/(?P<capacities>(A|C|E|H|I|L|P|S|X|B1|B2|U1|U2|V1|V2|D1|G1)+))"
    r"(?P<dep_ad_and_dep_time>((?P<dep_ad>[A-Z]{4})|AFIL|ZZZZ)(?P<eobt>((0|1)[0-9]|2[0-3])[0-5][0-9]))"
    r"(?P<cruising_speed>(K(0|1)[\d]{3})|(N0[\d]{3})|(M(0[\d]{2}|10\d)))"
    r"(?P<cruising_level>(F[\d]{2}[0,5])|(S[\d]{3}0)|(A[\d]{2}[0,5])|(M[\d]{4}))"
    r"(?P<sid_star>(?P<ats_point>[A-Z]{2,5})[\d][A-Z])"
    r"(?P<ats_route>[A-Z]{1,3}[\d]{1,3})"
    r"(?P<degrees>(([0-8]\d)|90)(N|S)((0[\d]{2})|(1[0-7]\d)|180)(E|W))"
    r"(?P<degrees_and_minutes>(([0-8]\d)|90)[0-5]\d(N|S)((0[\d]{2})|(1[0-7]\d)|180)[0-5]\d(E|W))+))",
    r"(?P<bearing_and_distance>[A-Z]{2,3}((0[\d]{2})|(1[0-7]\d)|180)[0-2][\d]{2})",
    r"(?P<sig_point>(?P=ats_point)|(?P=degrees)|(?P=degrees_and_minutes)|(?P=bearing_and_distance))",
    r"(?P<change_of_speed_or_level>(?P=sig_point)\/(?P=cruising_speed)(?P=cruising_level))",
    r"(?P<change_of_flight_rules>((?P=sig_point)|(?P=change_of_speed_or_level))\s(VFR|IFR))",
    r"(?P<cruise_climb>C\/(?P=sig_point)\/(?P=cruising_speed)(?P=cruising_level)((?P=cruising_level)|PLUS))",
    r"(?P<destination_ad_and_teet>(?P=aerodrome)[\d]{4})",
    r"(?P<no_other_information>0)",
    r"(?P<sts>STS\/(ALTRV|ATFMX|FFR|FLTCK|HAZMAT|HEAD|HOSP|HUM|MARSA|MEDEVAC|NONRVSM|SAR|STATE))",
    r"(?P<rnav_specifications>(A1|B[1-6]|C[1-4]|D[1-4]){1,4})",
    r"(?P<rnp_specifications>(L1|O[1-4]|S[1-2]|T[1-2]){1,4})",
    r"(?P<pbn>PBN\/(?P=rnav_specifications)(?P=rnp_specifications))",
    r"(?P<nav>NAV\/(SBAS|GBAS|ABAS|DGNSS|RTK|WARTK|PPP)(\s(SBAS|GBAS|ABAS|DGNSS|RTK|WARTK|PPP))?)",
    r"(?P<com>COM\/[A-Z\d]+)", r"(?P<dat>DAT\/[A-Z\d]+)",
    r"(?P<sur>SUR\/(RSP[\d]{3})(\sRSP[\d]{3})?)",
    r"(?P<dep>DEP\/(?P=aerodrome)|(?P=degrees_and_minutes)|(?P=bearing_and_distance)|(?P=ats_point))")

SAMPLE_FPL = ("ACF402-IN-EA30/H-S/C-EHAM0940-"
              "K0830F290 LEK2B LEK UA6 XMM/MO78F330 UA6 PON URION "
              "CHW UA5 NTS DCT 4611N00412W DCT STG UA5 FTM FATIM1A-"
              "LPPT0230 LPPR -REG/FBVGA SEL/EJFL EET/LPPCO158-E/0345 "
              "P/300 R/UVE S/PDJ J/UV D/11 330 C YELLOW A/WHITE C/DENKE")
