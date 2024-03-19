from django.contrib import admin

from apps.general.forms import FlightPlanForm
from apps.general.models import FlightPlan


@admin.register(FlightPlan)
class FlightPlanAdmin(admin.ModelAdmin):
    form = FlightPlanForm
    readonly_fields = ["date_of_flight"]
