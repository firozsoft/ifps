from import_export import fields, widgets

from apps.aerodromes.models.aerodrome import Aerodrome
from apps.general.admin.resources import BaseResource
from apps.points.models.navaid import NavAid
from apps.points.models.point import Point
from apps.routes.models.base import Route
from apps.routes.models.route_scheme import RouteScheme
from apps.routes.models.route_section import RouteSection
from apps.routes.models.sid_star import SidStar
from core.utils.choices import NavAidType, NavAidUseCase


class RouteResource(BaseResource):
    class Meta:
        model = Route


class RouteSectionResource(BaseResource):
    route = fields.Field(
        column_name="route",
        attribute="route",
        widget=widgets.ForeignKeyWidget(Route, field="indicator"),
    )
    point1 = fields.Field(
        column_name="point1",
        attribute="point1",
        widget=widgets.ForeignKeyWidget(Point, field="indicator"),
    )
    point2 = fields.Field(
        column_name="point2",
        attribute="point2",
        widget=widgets.ForeignKeyWidget(Point, field="indicator"),
    )

    class Meta:
        model = RouteSection


class RouteSchemeResource(BaseResource):
    class Meta:
        model = RouteScheme


class SidStarResource(BaseResource):
    class NavAidForeignKeyWidget(widgets.ForeignKeyWidget):
        def clean(self, value, row, **kwargs):
            if value:
                # Split the composite key into its components
                indicator, nv_type, usecase = (value.strip() for value in value.split("-"))
                nv_type = next(
                    choice_value
                    for choice_value, choice_label in NavAidType.choices
                    if choice_label == nv_type
                )
                usecase = next(
                    choice_value
                    for choice_value, choice_label in NavAidUseCase.choices
                    if choice_label == usecase
                )
                navaid, _ = NavAid.objects.get_or_create(indicator=indicator, type=nv_type, usecase=usecase)
                return navaid

    aerodrome = fields.Field(
        column_name="aerodrome",
        attribute="aerodrome",
        widget=widgets.ForeignKeyWidget(Aerodrome, field="indicator"),
    )
    point = fields.Field(
        column_name="point",
        attribute="point",
        widget=widgets.ForeignKeyWidget(Point, field="indicator"),
    )
    navaid = fields.Field(
        attribute="navaid",
        widget=NavAidForeignKeyWidget(NavAid, field="unique_indicator"),
    )

    class Meta(BaseResource.Meta):
        model = SidStar
        export_order = [
            "id",
            "indicator",
            "plain_language_name",
            "aerodrome",
            "point",
            "navaid",
            "type",
            "is_active",
            "rnp_app",
            "remarks",
        ]
