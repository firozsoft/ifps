import copy
from unittest import mock

from django.conf import settings
from django.test import TestCase

from apps.general.models.base import FIR
from apps.points.models.point import Point
from apps.routes.models.base import Route
from apps.routes.models.route_section import RouteSection
from core.analyzers import error_messages
from core.analyzers.route_analysis import (
    retrieve_point_name_from_fpl_route_section,
    retrieve_points_used_to_locate_ad_in_item18,
    route_analyzer,
)

OUR_FIR_INDICATOR = settings.FIR_INDICATOR


class RouteAnalyzerTestCase(TestCase):
    def setUp(self):
        self.data = dict()
        self.data["domestic_departure"] = False
        self.data["domestic_destination"] = False
        self.data["departure_ad"] = "OKAK"
        self.data["destination_ad"] = "VADB"
        self.data["eet"] = "OKKK0030 OIIX0100 OPKR0220 VAHH0330"
        self.data["route"] = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
            },
            {
                "from": "CAK",
                "to": "NANPI",
                "via": "G666",
            },
            {
                "from": "NANPI",
                "to": "SYZ",
                "via": "G666",
            },
            {
                "from": "SYZ",
                "to": "ASVIB",
                "via": "A452",
            },
            {
                "from": "ASVIB",
                "to": "PG",
                "via": "A452",
            },
        ]

        self.data_domestic = dict()
        self.data_domestic["domestic_departure"] = True
        self.data_domestic["domestic_destination"] = True
        self.data_domestic["departure_ad"] = "OISS"
        self.data_domestic["destination_ad"] = "OIII"
        self.data_domestic["route"] = [
            {
                "from": "SYZ",
                "to": "ISN",
                "via": "P574",
            },
            {
                "from": "ISN",
                "to": "BOXAM",
                "via": "B141",
            },
        ]

        our_fir = FIR.objects.create(indicator="OIIX")
        previous_fir = FIR.objects.create(indicator="OKKK")
        next_fir = FIR.objects.create(indicator="OPKR")
        nonneighbor_fir = FIR.objects.create(indicator="VAHH")

        cak = Point.objects.create(indicator="CAK", coordinate="4602N07805W")
        cak.fir.add(previous_fir)
        nanpi = Point.objects.create(indicator="NANPI", coordinate="4602N07806W", is_fir_boundary=True)
        nanpi.fir.add(previous_fir, our_fir)
        syz = Point.objects.create(indicator="SYZ", coordinate="4602N07807W")
        syz.fir.add(our_fir)
        isn = Point.objects.create(indicator="ISN", coordinate="4602N07817W")
        isn.fir.add(our_fir)
        boxam = Point.objects.create(indicator="BOXAM", coordinate="4602N07827W")
        boxam.fir.add(our_fir)
        asvib = Point.objects.create(indicator="ASVIB", coordinate="4602N07808W", is_fir_boundary=True)
        asvib.fir.add(our_fir, next_fir)
        pg = Point.objects.create(indicator="PG", coordinate="4602N07809W")
        pg.fir.add(next_fir)
        non = Point.objects.create(indicator="NON", coordinate="4602N07800W")
        non.fir.add(nonneighbor_fir)

        self.points = (cak, nanpi, syz, isn, boxam, asvib, pg, non)

        r1 = Route.objects.create(indicator="G666")
        r2 = Route.objects.create(indicator="A452")
        r3 = Route.objects.create(indicator="T215")
        r4 = Route.objects.create(indicator="P574")
        r5 = Route.objects.create(indicator="B141")

        RouteSection.objects.create(route=r1, point1=cak, point2=nanpi)
        RouteSection.objects.create(route=r1, point1=nanpi, point2=syz)
        RouteSection.objects.create(route=r2, point1=syz, point2=asvib)
        RouteSection.objects.create(route=r2, point1=asvib, point2=pg)
        RouteSection.objects.create(route=r2, point1=pg, point2=non)

        # a very long route to ignore lots of points if fpl
        RouteSection.objects.create(route=r3, point1=cak, point2=nanpi)
        RouteSection.objects.create(route=r3, point1=nanpi, point2=syz)
        RouteSection.objects.create(route=r3, point1=syz, point2=asvib)
        RouteSection.objects.create(route=r3, point1=asvib, point2=non)

        # domestic route
        RouteSection.objects.create(route=r4, point1=syz, point2=isn)
        RouteSection.objects.create(route=r5, point1=isn, point2=boxam)

    def test_retrieve_point_name_from_fpl_route(self):
        result = retrieve_point_name_from_fpl_route_section(
            self.data["route"], self.data["departure_ad"], self.data["destination_ad"]
        )
        self.assertSetEqual(result, {"CAK", "NANPI", "SYZ", "ASVIB", "PG"})

    def test_retrieve_points_used_to_locate_ad_in_item18(self):
        self.data["domestic_departure"] = True
        self.data["domestic_destination"] = True
        self.data["dep"] = "SYZ120030"
        self.data["dest"] = "YZD020060"
        self.data["departure_ad"] = "ZZZZ"
        self.data["destination_ad"] = "ZZZZ"
        self.data["alt_ad_1"] = "ZZZZ"
        self.data["alt_ad_2"] = "ZZZZ"
        self.data["altn"] = "TRN020060"
        self.data["ralt"] = "DNZ020060"

        result = retrieve_points_used_to_locate_ad_in_item18(self.data)

        self.assertSetEqual(result, {"SYZ", "YZD", "TRN", "DNZ"})

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_eet_missing_our_fir(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None
        data = copy.deepcopy(self.data)
        err = {"logical_error": []}
        data["eet"] = "OKKK0030 OPKR0220 VAHH0330"
        route_analyzer(data, err)
        self.assertDictEqual(
            err, {"logical_error": [error_messages.FIR_NOT_FOUND_IN_EET.format(OUR_FIR_INDICATOR)]}
        )

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_eet_missing_previous_fir_dep_not_in_adjacent(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None
        data = copy.deepcopy(self.data)
        err = {"logical_error": []}
        data["eet"] = "OIIX0100 OPKR0220 VAHH0330"
        data["departure_ad"] = "LTFM"
        route_analyzer(data, err)
        self.assertDictEqual(
            err,
            {
                "logical_error": [
                    error_messages.BOUNDARY_DETERMINATION_ERROR_NO_ADJACENT_FIRS.format(
                        "Entry", OUR_FIR_INDICATOR
                    )
                ]
            },
        )

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_eet_missing_next_fir(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None
        data = copy.deepcopy(self.data)
        err = {"logical_error": []}
        data["eet"] = "OKKK0030 OIIX0100 VAHH0330"
        route_analyzer(data, err)
        self.assertDictEqual(
            err,
            {
                "logical_error": [
                    error_messages.BOUNDARY_DETERMINATION_ERROR_NONADJACENT_FIR_OR_NO_BOUNDARY.format(
                        "VAHH", OUR_FIR_INDICATOR
                    )
                ]
            },
        )

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_pass_eet_missing_previous_fir_but_dep_in_adjacent_fir(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None
        data = copy.deepcopy(self.data)
        err = {"logical_error": []}
        data["eet"] = "OIIX0100 OPKR0220 VAHH0330"
        route_analyzer(data, err)
        self.assertDictEqual(err, {"logical_error": []})

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_pass_long_route(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None

        data = copy.deepcopy(self.data)
        data["route"] = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
            },
            {
                "from": "CAK",
                "to": "NON",
                "via": "T215",
            },
        ]
        err = {"logical_error": []}
        data["eet"] = "OIIX0210 OPKR0220 VAHH0330"

        # # Enable query counting
        # from django.db import connection

        # connection.force_debug_cursor = True

        route_analyzer(data, err)

        # # Output the number of queries
        # print(f"Total number of database queries: {len(connection.queries)}")
        # for query in connection.queries:
        #     print(query["sql"][:100])
        # # Disable query counting
        # connection.force_debug_cursor = False

        self.assertDictEqual(err, {"logical_error": []})

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_long_route_no_point_and_local_route(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None

        data = copy.deepcopy(self.data)
        data["route"] = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
            },
            {
                "from": "CAK",
                "to": "NON",
                "via": "P574",
            },
        ]
        err = {"logical_error": []}
        data["eet"] = "OKKK0030 OIIX0210 OPKR0220 VAHH0330"

        route_analyzer(data, err)

        self.assertIn(
            error_messages.BOUNDARY_DETERMINATION_ERROR_FROM_TO_FIR_ON_ROUTE.format(
                "Entry", "from", "OKKK", "P574"
            ),
            err["logical_error"],
        )

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_long_route_no_point_wrong_reginal_route_to_enter(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None

        data = copy.deepcopy(self.data)
        data["route"] = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
            },
            {
                "from": "CAK",
                "to": "NON",
                "via": "A452",
            },
        ]
        err = {"logical_error": []}
        data["eet"] = "OKKK0030 OIIX0210 OPKR0220 VAHH0330"

        route_analyzer(data, err)

        self.assertIn(
            error_messages.BOUNDARY_DETERMINATION_ERROR_FROM_TO_FIR_ON_ROUTE.format(
                "Entry", "from", "OKKK", "A452"
            ),
            err["logical_error"],
        )

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_long_route_no_point_wrong_reginal_route_to_exit(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None

        data = copy.deepcopy(self.data)
        data["route"] = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
            },
            {
                "from": "CAK",
                "to": "NON",
                "via": "G666",
            },
        ]
        err = {"logical_error": []}
        data["eet"] = "OKKK0030 OIIX0210 OPKR0220 VAHH0330"

        route_analyzer(data, err)

        self.assertIn(
            error_messages.BOUNDARY_DETERMINATION_ERROR_FROM_TO_FIR_ON_ROUTE.format(
                "Exit", "to", "OPKR", "G666"
            ),
            err["logical_error"],
        )

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_long_nonexisting_route(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None

        data = copy.deepcopy(self.data)
        data["route"] = [
            {
                "from": "OKBK",
                "to": "NANPI",
                "via": "LEK2B",
            },
            {
                "from": "NANPI",
                "to": "ASVIB",
                "via": "T21",
            },
        ]
        err = {"logical_error": []}
        data["eet"] = "OKKK0030 OIIX0210 OPKR0220 VAHH0330"
        route_analyzer(data, err)
        self.assertIn(error_messages.ROUTE_DOES_NOT_EXIST.format("T21"), err["logical_error"])

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_no_exit_point_no_long_route(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None

        data = copy.deepcopy(self.data)
        data["route"] = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
            },
            {
                "from": "CAK",
                "to": "ISN",
                "via": "T215",
            },
        ]
        err = {"logical_error": []}
        data["eet"] = "OIIX0210 OPKR0220 VAHH0330"
        # # Enable query counting
        # from django.db import connection

        # connection.force_debug_cursor = True

        route_analyzer(data, err)

        # # Output the number of queries
        # print(f"Total number of database queries: {len(connection.queries)}")
        # for query in connection.queries:
        #     print(query["sql"][:100])
        # # Disable query counting
        # connection.force_debug_cursor = False

        self.assertDictEqual(
            err,
            {
                "logical_error": [
                    error_messages.BOUNDARY_DETERMINATION_ERROR.format("Exit", OUR_FIR_INDICATOR)
                ]
            },
        )

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_pass_domestic_flight(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None

        data = copy.deepcopy(self.data_domestic)
        err = {"logical_error": []}
        route_analyzer(data, err)
        self.assertDictEqual(err, {"logical_error": []})

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_domestic_flight_nonexisting_route(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None

        data = copy.deepcopy(self.data_domestic)
        data["route"][0]["via"] = "P57"
        err = {"logical_error": []}

        route_analyzer(data, err)

        self.assertIn(error_messages.ROUTE_DOES_NOT_EXIST.format("P57"), err["logical_error"])
        self.assertIn(error_messages.PATH_NOT_FOUND.format("SYZ", "ISN", "P57"), err["logical_error"])

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_domestic_flight_nonexisting_point(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None

        data = copy.deepcopy(self.data_domestic)
        data["route"][0]["to"] = "TRN"
        err = {"logical_error": []}

        route_analyzer(data, err)

        self.assertDictEqual(
            err,
            {
                "logical_error": [
                    error_messages.POINT_DOES_NOT_EXIST.format("TRN"),
                    error_messages.PATH_NOT_FOUND.format("SYZ", "TRN", "P574"),
                ]
            },
        )

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_domestic_flight_wrong_route(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None

        data = copy.deepcopy(self.data_domestic)
        data["route"][0]["via"] = "G666"
        err = {"logical_error": []}

        route_analyzer(data, err)

        self.assertIn(error_messages.PATH_NOT_FOUND.format("SYZ", "ISN", "G666"), err["logical_error"])

    @mock.patch("core.analyzers.route_analysis.validate_fpl_route_section")
    def test_fail_due_domestic_flight_wrong_point(self, mock_validate_fpl_route_section):
        mock_validate_fpl_route_section.side_effect = None

        data = copy.deepcopy(self.data_domestic)
        data["route"][0]["to"] = "ASVIB"
        err = {"logical_error": []}

        route_analyzer(data, err)

        self.assertIn(error_messages.PATH_NOT_FOUND.format("SYZ", "ASVIB", "P574"), err["logical_error"])
