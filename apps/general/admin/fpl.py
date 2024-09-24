from django.contrib import admin
from import_export.admin import ExportActionModelAdmin

from apps.general.forms import FlightPlanForm
from apps.general.models.fpl import FlightPlan


@admin.register(FlightPlan)
class FlightPlanAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    form = FlightPlanForm
    readonly_fields = ["date_of_flight"]
