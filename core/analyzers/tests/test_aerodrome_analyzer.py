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
from core.analyzers.aerodromes_analysis import aerodromes_analyzer
from core.utils.choices import AerodromeFlightType, AerodromeType, NavAidType, NavAidUseCase, SidStarType
from create_aircraft import main as create_aircrafts


class AerodromeAnalyzerTestCase(TestCase):
    """Testign functionalities of the aerodrome-analyzer mudole

    Aerodrome creation, Heliport acceptable types, Curfew, TemporaryClosure, DailyOperationalHours, SID/STARs
    """

    def setUp(self):
        self.err = {"logical_error": []}
        self.fpl = {
            "domestic_departure": True,
            "domestic_destination": True,
            "departure_ad": "OIII",
            "destination_ad": "OISS",
            "alt_ad_1": "OIFM",
            "flight_type": "G",
            "flight_rule": "I",
            "dof": "240324",
            "eobt": "0800",
            "teet": "0130",
            "aircraft_type": "A319",
            "route": [{"flight_rule": "I"}],
        }

        # Create Aircrafts as required for Heliports acceptable types
        create_aircrafts()

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
        now = datetime.datetime.now()
        self.curfew = Curfew.objects.create(aerodrome=oiii, start=now, end=now + datetime.timedelta(hours=2))

        # Create temp-closure, daily op-hours
        TemporaryClosure.objects.create(aerodrome=oiii, start=now, end=now + datetime.timedelta(hours=2))

        # Create Daily Operational Hours
        self.oiii_dop = DailyOperationalHour.objects.create(
            aerodrome=oiii,
            date=now.date(),
            start_time=datetime.time(hour=7, minute=00),
            end_time=datetime.time(hour=23, minute=59),
            vfr_start_time=datetime.time(hour=7, minute=30),
            vfr_end_time=datetime.time(hour=17, minute=00),
        )
        self.oinj_dop = DailyOperationalHour.objects.create(
            aerodrome=oinj,
            date=now.date(),
            start_time=datetime.time(hour=8, minute=00),
            end_time=datetime.time(hour=16, minute=00),
            vfr_start_time=datetime.time(hour=8, minute=30),
            vfr_end_time=datetime.time(hour=15, minute=00),
        )

        # Create some points for sid/star
        moxur = Point.objects.create(indicator="MOXUR", coordinate="4602N07805W")
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
            nav_aid=vr,
            type=SidStarType.STAR,
        )
        dhn1v = SidStar.objects.create(
            aerodrome=oiii,
            indicator="DHN1V",
            point=dhn,
            nav_aid=dhn,
            type=SidStarType.SID,
        )

        self.sidstars = {"moxur1a": moxur1a, "dhn1v": dhn1v}

    def test_missing_alternate_fails(self):
        fpl = {
            "departure_ad": self.aerodromes.get("oiii"),
            "destination_ad": self.aerodromes.get("oiss"),
            "alt_ad_1": None,
        }
        err = copy.deepcopy(self.err)

        aerodromes_analyzer(fpl, err)

        self.assertDictEqual(
            err,
            {
                "logical_error": [
                    "The Destination, Departure and at least one Alternate Aerodromes are mandatory."
                ]
            },
        )

    def test_fails_due_ad_acceptable_types_and_flight_rules(self):
        err = copy.deepcopy(self.err)
        fpl = copy.deepcopy(self.fpl)
        fpl["destination_ad"] = "OINJ"

        aerodromes_analyzer(fpl, err)

        self.assertDictEqual(
            err,
            {
                "logical_error": [
                    "OINJ is Heliport and isn't available for A319.",
                    "OINJ does not accept IFR.",
                ]
            },
        )

    def test_fails_due_alt_ad_acceptable_types_and_flight_rules(self):
        err = copy.deepcopy(self.err)
        fpl = copy.deepcopy(self.fpl)
        fpl["alt_ad_1"] = "OINJ"

        aerodromes_analyzer(fpl, err)

        self.assertDictEqual(
            err,
            {
                "logical_error": [
                    "OINJ is Heliport and isn't available for A319.",
                    "OINJ does not accept IFR.",
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
            {"logical_error": ["OIII is not active."]},
        )

    def test_fails_due_alt_ad_not_active(self):
        self.aerodromes.get("oifm").is_active = False
        self.aerodromes.get("oifm").save(update_fields=["is_active"])
        err = copy.deepcopy(self.err)
        aerodromes_analyzer(self.fpl, err)

        self.assertDictEqual(
            err,
            {"logical_error": ["OIFM is not active."]},
        )

    def test_fails_due_ad_opr_hours(self):
        self.fpl["eobt"] = "0600"
        err = copy.deepcopy(self.err)
        aerodromes_analyzer(self.fpl, err)
        string = f"({self.oiii_dop.start_time} & {self.oiii_dop.end_time})"
        self.assertIn(string, err["logical_error"][0])

    def test_fails_due_dep_ad_vfr_opr_hours(self):
        self.fpl["eobt"] = "0700"
        self.fpl["flight_rule"] = "V"
        err = copy.deepcopy(self.err)
        string = f"({self.oiii_dop.vfr_start_time} & {self.oiii_dop.vfr_end_time})"

        aerodromes_analyzer(self.fpl, err)

        self.assertIn(string, err["logical_error"][0])

    def test_fails_due_dest_ad_vfr_opr_hours(self):
        err = copy.deepcopy(self.err)
        fpl = copy.deepcopy(self.fpl)
        fpl["eobt"] = "1400"
        fpl["destination_ad"] = "OINJ"
        fpl["flight_rule"] = "V"
        fpl["route"] = [{"flight_rule": "V"}]
        fpl["aircraft_type"] = "B214"
        string = f"({self.oinj_dop.vfr_start_time} & {self.oinj_dop.vfr_end_time})"
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

        self.assertIn(string, err["logical_error"][0])

    def test_fails_due_sid_star_not_exists(self):
        err = copy.deepcopy(self.err)
        fpl = copy.deepcopy(self.fpl)
        fpl["sid"] = "nonexisting_sid"
        fpl["star"] = "nonexisting_star"

        aerodromes_analyzer(fpl, err)

        self.assertDictEqual(
            err,
            {
                "logical_error": [
                    "SID nonexisting_sid does not exist.",
                    "STAR nonexisting_star does not exist.",
                ]
            },
        )

    # TODO: more tests. SID/STAR, Curfew, TempClosure
