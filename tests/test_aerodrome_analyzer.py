import copy
import datetime

from django.test import TestCase

from apps.aerodromes.models.aerodrome import Aerodrome
from apps.aerodromes.models.curfew import Curfew
from apps.aerodromes.models.daily_opr import DailyOperationalHour
from apps.aerodromes.models.temp_closure import TemporaryClosure
from apps.points.models.navaid import NavAid
from apps.points.models.point import Point
from apps.routes.models.sid_star import SidStar
from core.analyzers.aerodromes_analyzer import aerodromes_analyzer
from core.utils import error_messages
from core.utils.choices import AerodromeFlightType, AerodromeType, NavAidType, NavAidUseCase, SidStarType
from create_aircraft import main as create_aircrafts


class AerodromeAnalyzerTestCase(TestCase):
    """Testign functionalities of the aerodrome-analyzer mudole

    Aerodrome creation, Heliport acceptable types, Curfew, TemporaryClosure, DailyOperationalHours, SID/STARs
    """

    def setUp(self):
        self.err = {"integrity_error": []}
        self.fpl = {
            "domestic_departure": True,
            "domestic_destination": True,
            "departure_ad": "OIII",
            "destination_ad": "OISS",
            "alt_ad_1": "OIFM",
            "flight_type": "G",
            "flight_rule": "I",
            "dof": datetime.datetime.today().strftime("%y%m%d"),
            "eobt": "0800",
            "teet": "0130",
            "type_of_aircraft": "A319",
            "route": [{"flight_rule": "I"}],
        }

        # Create some aerodromes
        oiii = Aerodrome.objects.create(
            indicator="OIII",
            coordinate="4602N07801W",
            type=AerodromeType.AIRPORT,
            ifr_vfr=AerodromeFlightType.IFR_VFR,
            is_international=True,
            aur=True,
        )
        oiss = Aerodrome.objects.create(
            indicator="OISS",
            coordinate="4602N07802W",
            type=AerodromeType.AIRPORT,
            ifr_vfr=AerodromeFlightType.IFR_VFR,
            is_international=True,
            aur=True,
        )
        oifm = Aerodrome.objects.create(
            indicator="OIFM",
            coordinate="4602N07823W",
            type=AerodromeType.AIRPORT,
            ifr_vfr=AerodromeFlightType.IFR_VFR,
            is_international=True,
            aur=True,
        )
        oinj = Aerodrome.objects.create(
            indicator="OINJ",
            coordinate="4602N07803W",
            type=AerodromeType.HELIPORT,
            ifr_vfr=AerodromeFlightType.VFR,
            is_international=False,
            aur=True,
        )

        self.aerodromes = {"oiii": oiii, "oiss": oiss, "oifm": oifm, "oinj": oinj}

        # Create curfew
        self.curfew = Curfew.objects.create(
            aerodrome=oiii,
            start=datetime.datetime.combine(datetime.datetime.today(), datetime.time(hour=22, minute=00)),
            end=datetime.datetime.combine(datetime.datetime.today(), datetime.time(hour=23, minute=59)),
        )

        # Create temp-closure, daily op-hours
        TemporaryClosure.objects.create(
            aerodrome=oiii,
            start=datetime.datetime.combine(datetime.datetime.today(), datetime.time(hour=17, minute=00)),
            end=datetime.datetime.combine(datetime.datetime.today(), datetime.time(hour=19, minute=00)),
        )

        # Create Daily Operational Hours
        self.oiii_dop = DailyOperationalHour.objects.create(
            aerodrome=oiii,
            date=datetime.datetime.today(),
            start_time=datetime.time(hour=7, minute=00),
            end_time=datetime.time(hour=23, minute=59),
            vfr_start_time=datetime.time(hour=7, minute=30),
            vfr_end_time=datetime.time(hour=17, minute=00),
        )
        self.oinj_dop = DailyOperationalHour.objects.create(
            aerodrome=oinj,
            date=datetime.datetime.today(),
            start_time=datetime.time(hour=8, minute=00),
            end_time=datetime.time(hour=16, minute=00),
            vfr_start_time=datetime.time(hour=8, minute=30),
            vfr_end_time=datetime.time(hour=15, minute=00),
        )

        # Create some points for sid/star
        moxur = Point.objects.create(indicator="MOXUR", coordinate="4602N07815W")
        dhn = Point.objects.create(indicator="DHN", coordinate="4602N07806W")

        # Create some nav.aids for sid/star
        vr = NavAid.objects.create(
            indicator="VR",
            coordinate="4602N07812W",
            type=NavAidType.DVOR,
            use_case=NavAidUseCase.IN_AIRPORT,
        )
        dhn = NavAid.objects.create(
            indicator="DHN",
            coordinate="4602N07811W",
            type=NavAidType.DVOR,
            use_case=NavAidUseCase.IN_ROUTE,
        )

        # Create SID/STAR objects for aerodromes
        moxur1a = SidStar.objects.create(
            aerodrome=oiii,
            indicator="MOXUR1A",
            point=moxur,
            navaid=vr,
            type=SidStarType.STAR,
        )
        dhn1v = SidStar.objects.create(
            aerodrome=oiii,
            indicator="DHN1V",
            point=dhn,
            navaid=dhn,
            type=SidStarType.SID,
        )

        self.sidstars = {"moxur1a": moxur1a, "dhn1v": dhn1v}

    def test_missing_alternate_fails(self):
        fpl = {
            "departure_ad": "OIII",
            "destination_ad": "OISS",
            "alt_ad_1": None,
        }
        err = copy.deepcopy(self.err)

        aerodromes_analyzer(fpl, err)

        self.assertDictEqual(
            err,
            {"integrity_error": [error_messages.DEST_DEP_ONE_ALT_REQUIRED]},
        )

    def test_fails_due_ad_acceptable_types_and_flight_rules(self):
        # Create Aircrafts as required for Heliports acceptable types
        create_aircrafts()
        err = copy.deepcopy(self.err)
        fpl = copy.deepcopy(self.fpl)
        fpl["destination_ad"] = "OINJ"

        aerodromes_analyzer(fpl, err)

        self.assertDictEqual(
            err,
            {
                "integrity_error": [
                    error_messages.AERODROME_INCOMPATIBLE_TYPE_OF_AIRCRAFT.format("OINJ", "heliport", "A319"),
                    error_messages.AERODROME_INCOMPATIBLE_FLIGHT_RULE.format("OINJ", "IFR"),
                ]
            },
        )

    def test_fails_due_alt_ad_acceptable_types_and_flight_rules(self):
        # Create Aircrafts as required for Heliports acceptable types
        create_aircrafts()
        err = copy.deepcopy(self.err)
        fpl = copy.deepcopy(self.fpl)
        fpl["alt_ad_1"] = "OINJ"

        aerodromes_analyzer(fpl, err)

        self.assertDictEqual(
            err,
            {
                "integrity_error": [
                    error_messages.AERODROME_INCOMPATIBLE_TYPE_OF_AIRCRAFT.format("OINJ", "heliport", "A319"),
                    error_messages.AERODROME_INCOMPATIBLE_FLIGHT_RULE.format("OINJ", "IFR"),
                ]
            },
        )

    def test_fails_due_ad_not_active(self):
        self.aerodromes.get("oiii").is_active = False
        self.aerodromes.get("oiii").save(update_fields=["is_active"])
        err = copy.deepcopy(self.err)
        aerodromes_analyzer(self.fpl, err)

        self.assertDictEqual(
            err,
            {"integrity_error": [error_messages.AERODROME_INACTIVE.format("OIII")]},
        )

    def test_fails_due_alt_ad_not_active(self):
        self.aerodromes.get("oifm").is_active = False
        self.aerodromes.get("oifm").save(update_fields=["is_active"])
        err = copy.deepcopy(self.err)

        aerodromes_analyzer(self.fpl, err)

        self.assertDictEqual(
            err,
            {"integrity_error": [error_messages.AERODROME_INACTIVE.format("OIFM")]},
        )

    def test_fails_due_sid_star_not_exists(self):
        err = copy.deepcopy(self.err)
        fpl = copy.deepcopy(self.fpl)
        fpl["sid"] = "nonexisting_sid"
        fpl["star"] = "nonexisting_star"

        aerodromes_analyzer(fpl, err)

        self.assertDictEqual(
            err,
            {
                "integrity_error": [
                    error_messages.SID_STAR_DOES_NOT_EXIST.format("SID", "nonexisting_sid"),
                    error_messages.SID_STAR_DOES_NOT_EXIST.format("STAR", "nonexisting_star"),
                ]
            },
        )

    # NOTE: Time Tests
    # OIII DOP:0700-2359, VOP:0730-1700, Curfew:2200-2359, TMC:1700-1900
    # OINJ DOP:0800-1600, VOP:0830-1500

    def test_fails_due_ad_opr_hours(self):
        self.fpl["eobt"] = "0600"
        err = copy.deepcopy(self.err)

        aerodromes_analyzer(self.fpl, err)

        self.assertTrue(err["integrity_error"])
        self.assertIn("is not in aerorome's operational hours", err["integrity_error"][0])

    def test_fails_due_dep_ad_vfr_opr_hours(self):
        self.fpl["eobt"] = "0700"
        self.fpl["flight_rule"] = "V"
        err = copy.deepcopy(self.err)

        aerodromes_analyzer(self.fpl, err)

        self.assertIn("is not in aerorome's operational hours", err["integrity_error"][0])

    def test_fails_due_dest_ad_vfr_opr_hours(self):
        err = copy.deepcopy(self.err)
        fpl = copy.deepcopy(self.fpl)
        fpl["eobt"] = "1400"
        fpl["destination_ad"] = "OINJ"
        fpl["flight_rule"] = "V"
        fpl["route"] = [{"flight_rule": "V"}]
        fpl["type_of_aircraft"] = "B214"

        # # Enable query counting
        # from django.db import connection

        # connection.force_debug_cursor = True

        aerodromes_analyzer(fpl, err)

        # # Output the number of queries
        # print(f"Total number of database queries: {len(connection.queries)}")
        # for query in connection.queries:
        #     print(query["sql"][:100])
        # # Disable query counting
        # connection.force_debug_cursor = False

        self.assertIn("is not in aerorome's operational hours", err["integrity_error"][0])

    def test_fails_due_dep_ad_temp_closure(self):
        # Curfew:2200-2359, TMC:1700-1900
        self.fpl["eobt"] = "1800"
        err = copy.deepcopy(self.err)

        aerodromes_analyzer(self.fpl, err)

        self.assertTrue(err["integrity_error"])
        self.assertIn("temporarily closed", err["integrity_error"][0])

    def test_fails_due_dest_ad_temp_closure(self):
        # Curfew:2200-2359, TMC:1700-1900
        err = copy.deepcopy(self.err)
        self.fpl["eobt"] = "1600"
        self.fpl["teet"] = "0130"
        self.fpl["departure_ad"] = "OISS"
        self.fpl["destination_ad"] = "OIII"

        aerodromes_analyzer(self.fpl, err)

        self.assertTrue(err["integrity_error"])
        self.assertIn("temporarily closed", err["integrity_error"][0])

    def test_pass_ad_temp_closure_not_meet(self):
        # Curfew:2200-2359, TMC:1700-1900
        self.fpl["eobt"] = "1659"
        err = copy.deepcopy(self.err)

        aerodromes_analyzer(self.fpl, err)

        self.assertFalse(err["integrity_error"])

    def test_fails_due_dep_ad_curfew(self):
        # Curfew:2200-2359, TMC:1700-1900
        self.fpl["eobt"] = "2200"
        err = copy.deepcopy(self.err)

        aerodromes_analyzer(self.fpl, err)

        self.assertTrue(err["integrity_error"])
        self.assertIn("curfew time", err["integrity_error"][0])

    def test_fails_due_dest_ad_curfew(self):
        # Curfew:2200-2359, TMC:1700-1900
        err = copy.deepcopy(self.err)
        self.fpl["eobt"] = "2100"
        self.fpl["teet"] = "0130"
        self.fpl["departure_ad"] = "OISS"
        self.fpl["destination_ad"] = "OIII"

        aerodromes_analyzer(self.fpl, err)

        self.assertTrue(err["integrity_error"])
        self.assertIn("curfew time", err["integrity_error"][0])

    def test_pass_dest_ad_curfew_not_meet(self):
        # Curfew:2200-2359, TMC:1700-1900
        err = copy.deepcopy(self.err)
        self.fpl["eobt"] = "2300"
        self.fpl["teet"] = "0130"
        self.fpl["departure_ad"] = "OISS"
        self.fpl["destination_ad"] = "OIII"

        aerodromes_analyzer(self.fpl, err)

        self.assertTrue(err["integrity_error"])
        self.assertIn("is not in aerorome's operational hours", err["integrity_error"][0])
