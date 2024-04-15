from import_export import fields, widgets

from apps.aerodromes.models.aerodrome import Aerodrome
from apps.aerodromes.models.curfew import Curfew
from apps.aerodromes.models.daily_opr import DailyOperationalHour
from apps.aerodromes.models.temp_closure import TemporaryClosure
from apps.general.admin.resources import BasePointResource, BaseResource


class AerodromeResource(BasePointResource):
    class Meta:
        model = Aerodrome
        export_order = [
            "id",
            "indicator",
            "plain_language_name",
            "iatacode",
            "coordinate",
            "latitude",
            "longitude",
            "fir",
            "is_fir_boundary",
            "type",
            "ifr_vfr",
            "is_international",
            "aur",
            "is_active",
        ]


class AerodromePropertiesResource(BaseResource):
    aerodrome = fields.Field(
        column_name="aerodrome",
        attribute="aerodrome",
        widget=widgets.ForeignKeyWidget(Aerodrome, field="indicator"),
    )

    def get_export_order(self):
        order = list(super().get_export_order())
        order.insert(4, order.pop(order.index("is_active")))
        return tuple(order)


class DailyOperationalHourResource(AerodromePropertiesResource):
    class Meta:
        model = DailyOperationalHour
        widgets = {
            "date": {"format": "%Y%m%d"},
            "start_time": {"format": "%H%M"},
            "end_time": {"format": "%H%M"},
            "vfr_start_time": {"format": "%H%M"},
            "vfr_end_time": {"format": "%H%M"},
        }

    def get_export_order(self):
        order = list(super().get_export_order())
        order.insert(0, order.pop(order.index("id")))
        return tuple(order)


class CurfewResource(AerodromePropertiesResource):
    class Meta:
        model = Curfew
        widgets = {
            "start": {"format": "%H%M"},
            "end": {"format": "%H%M"},
        }


class TempClosureResource(AerodromePropertiesResource):
    class Meta:
        model = TemporaryClosure
        widgets = {
            "start": {"format": "%H%M"},
            "end": {"format": "%H%M"},
        }
