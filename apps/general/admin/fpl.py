from datetime import datetime

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpResponse

from apps.general.forms import FlightPlanForm
from apps.general.models.fpl import FlightPlan
from core.utils.helpers import model_to_excel_bytesio


def export_selected_items(modeladmin, request, queryset: QuerySet):
    model_name = queryset.model.__name__.lower()
    excel_buffer = model_to_excel_bytesio(model_name, queryset)
    # Set the appropriate HTTP headers for the response
    response = HttpResponse(
        excel_buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Set the filename for the response (optional)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    response["Content-Disposition"] = f'attachment; filename="{model_name}-{timestamp}.xlsx"'

    return response


export_selected_items.short_description = "Export selected items"


@admin.register(FlightPlan)
class FlightPlanAdmin(admin.ModelAdmin):
    form = FlightPlanForm
    readonly_fields = ["date_of_flight"]
    actions = [export_selected_items]
