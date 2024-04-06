from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.points.models.point import Point
from apps.routes.models.base import Route
from apps.routes.models.route_section import RouteSection
from core.analyzers.route_analysis import find_all_nested_real_sections


class FindRealRouteSectionsTestCase(TestCase):
    def setUp(self):
        self.fpl_route = [
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
        ]

        nanpi = Point.objects.create(indicator="NANPI", coordinate="4602N07806W", is_fir_boundary=True)
        syz = Point.objects.create(indicator="SYZ", coordinate="4602N07807W")
        asvib = Point.objects.create(indicator="ASVIB", coordinate="4602N07808W", is_fir_boundary=True)

        r1 = Route.objects.create(indicator="G666")
        r2 = Route.objects.create(indicator="A452")
        RouteSection.objects.create(route=r1, point1=nanpi, point2=syz)
        RouteSection.objects.create(route=r2, point1=syz, point2=asvib)

        self.fpl_route_sections = [
            route_section
            for route_section in self.fpl_route
            if "nonessential" not in route_section or (route_section["via"] not in ("", "DCT"))
        ]

        self.existing_sections = RouteSection.objects.filter(
            route__indicator__in=set(section["via"] for section in self.fpl_route_sections)
        ).select_related("route", "point1", "point2")

        self.existing_sections_dict = {
            (sec.route.indicator, sec.point1.indicator, sec.point2.indicator): sec
            for sec in self.existing_sections
        }

    def test_fund_all_nested_real_sections(self):
        fpl_route_section = {
            "from": "NANPI",
            "to": "SYZ",
            "via": "G666",
        }
        result = find_all_nested_real_sections(fpl_route_section, self.existing_sections_dict)
        self.assertListEqual(result, [("G666", "NANPI", "SYZ")])

    def test_exception_raised_wrong_point(self):
        fpl_route_section = {
            "from": "NANPI",
            "to": "ASVIB",
            "via": "G666",
        }
        with self.assertRaises(ValidationError):
            find_all_nested_real_sections(fpl_route_section, self.existing_sections_dict)

    def test_exception_raised_wrong_route(self):
        fpl_route_section = {
            "from": "NANPI",
            "to": "SYZ",
            "via": "A452",
        }
        with self.assertRaises(ValidationError):
            find_all_nested_real_sections(fpl_route_section, self.existing_sections_dict)
