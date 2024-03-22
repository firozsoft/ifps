from django.test import TestCase

from apps.general.models.base import FIR
from apps.points.models.point import Point
from core.analyzers.route_analysis import (
    retrieve_point_name_from_fpl_route_section,
    retrieve_points_used_to_locate_ad_in_item18,
)


class RetrievePointsTestCase(TestCase):
    def setUp(self):
        self.data = dict()
        self.data["eet"] = "OKKK0030 OIIX0100 OPKC0220 VAHH0330"
        self.err = {"logical_error": []}
        self.data["departure_ad"] = "OKBK"
        self.data["destination_ad"] = "VAHH"
        self.data["route"] = [
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

        self.our_fir = FIR.objects.create(indicator="OIIX")
        self.previous_fir = FIR.objects.create(indicator="OKKK")
        self.next_fir = FIR.objects.create(indicator="OPKC")
        self.nonneighbor_fir = FIR.objects.create(indicator="VAHH")

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

        self.points = (cak, nanpi, syz, asvib, pg, non)

        self.existing_points = {
            point.indicator: (point, set(point.fir.values_list("indicator", flat=True)))
            for point in Point.objects.filter(
                indicator__in=[p.indicator for p in self.points]
            ).prefetch_related("fir")
        }

    def test_retrieve_point_name_from_fpl_route(self):
        result = retrieve_point_name_from_fpl_route_section(self.data)
        points = set(map(lambda x: x.indicator, self.points))
        points.discard("NON")
        self.assertSetEqual(result, points)

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
