from apps.general.admin.resources import BasePointResource
from apps.points.models.navaid import NavAid
from apps.points.models.point import Point


class PointResource(BasePointResource):
    class Meta:
        model = Point
        export_order = [
            "id",
            "indicator",
            "plain_language_name",
            "is_active",
            "coordinate",
            "latitude",
            "longitude",
            "fir",
            "is_fir_boundary",
        ]

    def filter_export(self, queryset, *args, **kwargs):
        # Do not export NavAid instances, NavAid is subclass of Point
        return super().filter_export(queryset, *args, **kwargs).exclude(navaid__isnull=False)


class NavAidResource(BasePointResource):
    class Meta:
        model = NavAid
        exclude = ["point_ptr", "created", "updated"]
        export_order = [
            "id",
            "indicator",
            "plain_language_name",
            "type",
            "usecase",
            "is_active",
            "coordinate",
            "latitude",
            "longitude",
            "fir",
            "is_fir_boundary",
        ]
