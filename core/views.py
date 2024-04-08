import copy
import io
import json
import zipfile
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import CreateView

from apps.general.forms import FlightPlanForm
from apps.general.models.fpl import FlightPlan
from core.analyzers import parser
from core.analyzers.integrity_analyzer import main
from core.utils.helpers import (
    get_app_all_exportable_models_with_restriction,
    model_to_excel_bytesio,
)


class CustomLoginView(LoginView):
    template_name = "pages/login.html"
    success_url = "/"


class FlightPlanCreateView(LoginRequiredMixin, CreateView):
    model = FlightPlan
    form_class = FlightPlanForm
    template_name = "pages/fpl.html"

    def form_valid(self, form):
        row_data = copy.deepcopy(form.changed_data)
        row_data["flt_rule_type"] = row_data["flight_rule"] + row_data["type_of_flight"]
        row_data["numbers_type_weak"] = (
            row_data["number_of_aircraft"]
            + row_data["type_of_aircraft"]
            + row_data["weakturbulence_category"]
        )
        row_data["dep_ad_time"] = row_data["departure_aerodrome"] + row_data["departure_time"]
        row_data["route"] = row_data["cruising_speed"] + row_data["cruising_level"] + " " + row_data["route"]
        row_data["dest_teet_alts"] = (
            row_data["destination_aerodrome"]
            + row_data["teet"]
            + " "
            + row_data["alternate_aerodrome"]
            + " "
            + row_data["secind_alternate_aerodrome"]
        )
        row_data["others"] = "DOF/" + row_data["date_of_flight"] + row_data["other_information"]

        fpl, err = parser.parse(row_data)
        if err:
            form.add_error(err)
            return self.form_invalid(form)

        err = main(fpl)
        if err:
            form.add_error(err)
            return self.form_invalid(form)

        return super().form_valid(form)


def fpl_scrutinization(request, msg: str) -> JsonResponse:
    parts = list(map(str.strip, msg.split("-")))

    if len(parts) < 9:
        return JsonResponse(
            {"syntax_error": "FPL message must have at least 9 sections separated by hyphens."}, status=400
        )

    filled_data = {
        # "msg_type": parts[0], #-> (FPL
        "aircraft_identification": parts[1],
        "flt_rule_type": parts[2],
        "numbers_type_weak": parts[3],
        "equipments_and_capacities": parts[4],
        "dep_ad_time": parts[5],
        "route": parts[6],
        "dest_teet_alts": parts[7],
        "others": parts[8].replace(")", ""),
        # 'extra': parts[9]
    }

    fpl, err = parser.parse(filled_data)
    if err:
        return JsonResponse(err, status=400)

    err = main(fpl)
    if err:
        return JsonResponse(err, status=400)
        # return render(request, "pages/index.html", {"data": json.dumps(err)})

    return render(request, "pages/index.html", {"data": json.dumps(fpl)})


@login_required
@require_http_methods(["POST"])
def submission(request: HttpRequest) -> JsonResponse:
    msg = request.POST.get(key="message", default=None)
    if not msg:
        return JsonResponse({"Error": "field message is missing", "error_code": "msg_not_found"}, status=400)
    if msg.startswith("(FPL"):
        return fpl_scrutinization(request, msg)
    return JsonResponse({"Error": "text must be an AFTN FPL message"}, status=400)


@staff_member_required
def export_models(request: HttpRequest) -> HttpResponse:
    """
    It exports the data of all models of this project to Excel files and returns
    a ZIP archive containing the Excel files as an HTTP response.
    """
    model_names = get_app_all_exportable_models_with_restriction("apps.")

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")

    # Create a BytesIO object to store the ZIP archive
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for model_name in model_names:
            excel_buffer = model_to_excel_bytesio(model_name)
            zip_file.writestr(f"{model_name}.xlsx", excel_buffer.getvalue())

    # Create an HttpResponse with the ZIP archive content
    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")

    # Set the filename for the response
    response["Content-Disposition"] = f'attachment; filename="ifps-export-{timestamp}.zip"'

    return response


@staff_member_required
def export_model(request: HttpRequest, model_name: str) -> HttpResponse:
    """This method exports data from a model to an Excel file."""

    excel_buffer = model_to_excel_bytesio(model_name)

    # Set the appropriate HTTP headers for the response
    response = HttpResponse(
        excel_buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Set the filename for the response (optional)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    response["Content-Disposition"] = f'attachment; filename="{model_name}-{timestamp}.xlsx"'

    return response
