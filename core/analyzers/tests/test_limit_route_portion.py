from django.test import TestCase

from apps.general.models.base import FIR
from apps.points.models.point import Point
from apps.routes.models.base import Route
from apps.routes.models.route_section import RouteSection
from core.analyzers.limit_route_portion import successfully_limited_route_portion


class SuccessfullyLimitedRoutePortionTestCase(TestCase):
    def setUp(self):
        self.our_fir = FIR.objects.create(indicator="OIIX")
        self.previous_fir = FIR.objects.create(indicator="OKKK")
        self.next_fir = FIR.objects.create(indicator="OPKC")
        self.nonneighbor_fir = FIR.objects.create(indicator="VAHH")
        self.eet = "OKKK0030 OIIX0100 OPKC0220 VAHH0330"
        self.err = {"logical_error": []}
        self.fpl_route = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "CAK",
                "to": "NANPI",
                "via": "G666",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "NANPI",
                "to": "SYZ",
                "via": "G666",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "SYZ",
                "to": "ASVIB",
                "via": "A452",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "ASVIB",
                "to": "PG",
                "via": "A452",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
        ]

        cak = Point.objects.create(indicator="CAK", coordinate="4602N07805W")
        cak.fir.add(self.previous_fir)
        nanpi = Point.objects.create(indicator="NANPI", coordinate="4602N07806W", is_fir_boundary=True)
        nanpi.fir.add(self.previous_fir, self.our_fir)
        syz = Point.objects.create(indicator="SYZ", coordinate="4602N07807W")
        syz.fir.add(self.our_fir)
        asvib = Point.objects.create(indicator="ASVIB", coordinate="4602N07808W", is_fir_boundary=True)
        asvib.fir.add(self.our_fir, self.next_fir)
        pg = Point.objects.create(indicator="PG", coordinate="4602N07809W")
        pg.fir.add(self.next_fir)
        non = Point.objects.create(indicator="NON", coordinate="4602N07800W")
        non.fir.add(self.nonneighbor_fir)

        points = (cak, nanpi, syz, asvib, pg, non)

        self.existing_points = {
            point.indicator: (point, set(point.fir.values_list("indicator", flat=True)))
            for point in Point.objects.filter(indicator__in=[p.indicator for p in points]).prefetch_related(
                "fir"
            )
        }

        r1 = Route.objects.create(indicator="G666")
        r2 = Route.objects.create(indicator="A452")
        r3 = Route.objects.create(indicator="T215")
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

    def test_neighbor_fir_none(self):
        entry_or_exit = "Entry"

        result = successfully_limited_route_portion(
            self.our_fir, None, self.fpl_route, self.existing_points, entry_or_exit, self.eet, self.err
        )
        self.assertFalse(result)
        self.assertTrue(self.err["logical_error"])

    def test_no_common_boundaries(self):
        entry_or_exit = "Exit"

        result = successfully_limited_route_portion(
            self.our_fir,
            self.nonneighbor_fir,
            self.fpl_route,
            self.existing_points,
            entry_or_exit,
            self.eet,
            self.err,
        )
        self.assertFalse(result)
        self.assertTrue(self.err["logical_error"])

    def test_find_entry_boundary_mentioned(self):
        entry_or_exit = "Entry"

        route = successfully_limited_route_portion(
            self.our_fir,
            self.previous_fir,
            self.fpl_route,
            self.existing_points,
            entry_or_exit,
            self.eet,
            self.err,
        )
        self.assertEqual(
            route[0],
            {
                "from": "NANPI",
                "to": "SYZ",
                "via": "G666",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
        )

    def test_find_entry_boundary_not_mentioned(self):
        entry_or_exit = "Entry"
        fpl_route = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "CAK",
                "to": "SYZ",
                "via": "G666",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "SYZ",
                "to": "ASVIB",
                "via": "A452",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "ASVIB",
                "to": "PG",
                "via": "A452",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
        ]

        route = successfully_limited_route_portion(
            self.our_fir,
            self.previous_fir,
            fpl_route,
            self.existing_points,
            entry_or_exit,
            self.eet,
            self.err,
        )
        self.assertEqual(
            route[0],
            {
                "from": "NANPI",
                "to": "SYZ",
                "via": "G666",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
        )

    def test_find_exit_wrong_neighbor1(self):
        entry_or_exit = "Exit"
        fpl_route = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "CAK",
                "to": "SYZ",
                "via": "G666",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "SYZ",
                "to": "ASVIB",
                "via": "A452",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "ASVIB",
                "to": "PG",
                "via": "A452",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
        ]

        route = successfully_limited_route_portion(
            self.our_fir,
            self.previous_fir,
            fpl_route,
            self.existing_points,
            entry_or_exit,
            self.eet,
            self.err,
        )
        self.assertEqual(route, [])

    def test_find_exit_wrong_neighbor2(self):
        entry_or_exit = "Exit"
        fpl_route = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "CAK",
                "to": "SYZ",
                "via": "G666",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "SYZ",
                "to": "ASVIB",
                "via": "A452",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "ASVIB",
                "to": "PG",
                "via": "A452",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
        ]

        route = successfully_limited_route_portion(
            self.our_fir,
            self.nonneighbor_fir,
            fpl_route,
            self.existing_points,
            entry_or_exit,
            self.eet,
            self.err,
        )
        self.assertEqual(route, [])

    def test_find_exit(self):
        entry_or_exit = "Exit"

        route = successfully_limited_route_portion(
            self.our_fir,
            self.nonneighbor_fir,
            self.fpl_route,
            self.existing_points,
            entry_or_exit,
            self.eet,
            self.err,
        )
        self.assertEqual(route, [])

    def test_find_exit_boundary_not_mentioned(self):
        entry_or_exit = "Exit"
        fpl_route = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "CAK",
                "to": "SYZ",
                "via": "G666",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "SYZ",
                "to": "PG",
                "via": "A452",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
        ]

        route = successfully_limited_route_portion(
            self.our_fir,
            self.next_fir,
            fpl_route,
            self.existing_points,
            entry_or_exit,
            self.eet,
            self.err,
        )
        self.assertEqual(
            route[-1],
            {
                "from": "SYZ",
                "to": "ASVIB",
                "via": "A452",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
        )

    def test_find_entry_on_long_route(self):
        fpl_route = [
            {
                "from": "OKBK",
                "to": "CAK",
                "via": "LEK2B",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
            {
                "from": "CAK",
                "to": "NON",
                "via": "T215",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
        ]

        entry_or_exit = "Entry"
        route = successfully_limited_route_portion(
            self.our_fir,
            self.previous_fir,
            fpl_route,
            self.existing_points,
            entry_or_exit,
            self.eet,
            self.err,
        )
        self.assertEqual(
            route[0],
            {
                "from": "NANPI",
                "to": "NON",
                "via": "T215",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
        )

        entry_or_exit = "Exit"
        route = successfully_limited_route_portion(
            self.our_fir,
            self.next_fir,
            route,
            self.existing_points,
            entry_or_exit,
            self.eet,
            self.err,
        )
        self.assertEqual(
            # NOTE: index 0 is on purpose, long route with no point in our FIR results in a single section!
            route[0],
            {
                "from": "NANPI",
                "to": "ASVIB",
                "via": "T215",
                "speed": "K0830",
                "level": "F290",
                "top_level": "F290",
                "flight_rule": "I",
            },
        )
