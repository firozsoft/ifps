import copy
import io
import zipfile

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers import serialize
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import CreateView

from apps.general.forms import FlightPlanForm
from apps.general.models.fpl import FlightPlan
from core.analyzers import parser
from core.analyzers.integrity_analyzer import integrity_checks
from core.utils.helpers import (
    get_app_exportable_models,
    model_to_excel_bytesio,
)

FPL_EXPECTED_DASHES = 9


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

        err, notams = integrity_checks(fpl)
        if err:
            form.add_error(err)
            return self.form_invalid(form)

        return super().form_valid(form)


def user_has_subscription(user):
    return "Active" in user.userprofile.get_subscription_status()


@login_required(login_url="accounts:login")
@user_passes_test(user_has_subscription)
@require_http_methods(["POST"])
def submission(request: HttpRequest) -> JsonResponse:
    """Handle submission of FPL (Flight Plan) messages via a POST request.

    Validates and processes a submitted FPL message received via a POST request.

    Args:
    ----
        request (HttpRequest): The HTTP request object containing the submitted data.

    Returns:
    -------
        JsonResponse: A JSON response containing either a success message or an error message.

    Raises:
    ------
        Http404: If the request method is not POST or if the user is not authenticated, handled by decorators.

    Usage:
        This function is intended to be used as a handler for FPL message submissions made via a POST request.
        Example usage:
        ```python
        response = submission(request)
        ```

    Error Responses:
        - If the submitted message is empty or does not meet the required format,
          a JSON response with an appropriate error message and status code 400 (Bad Request) is returned.
        - If there are validation errors during FPL message parsing or integrity checks,
          the response includes error details and status code 400 (Bad Request).
        - If no errors are detected and the FPL message is processed successfully,
          a JSON response with status code 200 (OK) is returned along with any relevant NOTAMs.

    Notes:
    -----
        - Requires the user to be authenticated (logged in) via the `@login_required` decorator.
        - Expects a POST request, as specified by the `@require_http_methods(["POST"])` decorator.

    """
    msg = request.POST.get(key="message", default=None)
    if not msg:
        message = {
            "Error(s)": (
                "Empty message detected. Please provide a complete FPL message "
                f"with at least {FPL_EXPECTED_DASHES} sections separated by hyphens."
            ),
        }
        return JsonResponse(message, status=422)

    if not msg.startswith("(FPL"):
        message = {
            "Error(s)": (
                "Invalid message format. Please ensure the message begins with '(FPL' "
                f"and contains at least {FPL_EXPECTED_DASHES} sections separated by hyphens."
            ),
        }
        return JsonResponse(message, status=422)

    parts = list(map(str.strip, msg.split("-")))

    if len(parts) < FPL_EXPECTED_DASHES:
        message = {
            "Error(s)": (
                "Invalid FPL message format. Please provide a complete FPL message "
                f"with at least {FPL_EXPECTED_DASHES} sections separated by hyphens."
            ),
        }
        return JsonResponse(message, status=422)

    filled_data = {
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
        message = {"Error(s)": err}
        return JsonResponse(message, status=400)

    err, notams = integrity_checks(fpl)
    notams = serialize("json", notams) if notams else None

    if err:
        message = {"Error(s)": err}
        status_code = 400

    else:
        message = {"Success": "No errors detected."}
        status_code = 200

    if notams:
        if "Success" in message:
            message.pop("Success")
            message["Warning"] = "No errors detected. But review the considerable NOTAMs for further details."
        # Order of dict items matters - NOTAM(s) must be the last key of message
        message["NOTAM(s)"] = notams

    return JsonResponse(message, status=status_code)


@staff_member_required
def export_models(_: HttpRequest, app_label="") -> HttpResponse:
    """Export all models to Excel files and return a ZIP archive."""
    model_names = get_app_exportable_models(f"apps.{app_label}")

    timestamp = timezone.now().strftime("%Y-%m-%d-%H-%M")

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
def export_model(_: HttpRequest, model_name: str) -> HttpResponse:
    """Export data from a model to an Excel file."""
    excel_buffer = model_to_excel_bytesio(model_name)

    # Set the appropriate HTTP headers for the response
    response = HttpResponse(
        excel_buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Set the filename for the response (optional)
    timestamp = timezone.now().strftime("%Y-%m-%d-%H-%M")
    response["Content-Disposition"] = f'attachment; filename="{model_name}-{timestamp}.xlsx"'

    return response
