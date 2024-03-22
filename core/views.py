import io
import json
import zipfile
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from apps.general.forms import FlightPlanForm
from core.analyzers.logical_checks import logical_check
from core.analyzers.regexer import regex_parse
from core.utils.helpers import get_app_all_models, model_to_excel_bytesio


class CustomLoginView(LoginView):
    template_name = "pages/login.html"
    success_url = "/"


def fpl_scrutinization(request, msg: str) -> JsonResponse:
    parts = list(map(str.strip, msg.split("-")))

    if len(parts) < 9:
        return JsonResponse(
            {"syntax_error": "FPL message must have at least 9 sections separated by hyphens."}, status=400
        )

    filled_data = {
        # "msg_type": parts[0], #-> (FPL
        "call_sign": parts[1],
        "flt_rule_type": parts[2],
        "numbers_type_weak": parts[3],
        "equipments_and_capacities": parts[4],
        "dep_ad_time": parts[5],
        "route": parts[6],
        "dest_teet_alts": parts[7],
        "others": parts[8].replace(")", ""),
        # 'extra': parts[9]
    }

    try:
        res, err = regex_parse(filled_data)
    except Exception:
        return JsonResponse(
            {
                "internal_error": "Internal Server Error: Please notify the administration. And if possible, "
                "provide necessary data to assist in reproducing the issue for further investigation."
            },
            status=500,
        )

    if err:
        return JsonResponse(err, status=400)

    try:
        err = logical_check(res)
    except Exception:
        return JsonResponse(
            {
                "internal_error": "Internal Server Error: Please notify the administration. And if possible, "
                "provide necessary data to assist in reproducing the issue for further investigation."
            },
            status=500,
        )

    if err:
        # return JsonResponse(err, status=400)
        return render(request, "pages/index.html", {"data": json.dumps(err)})

    # TODO: use data of res (dict) and FlightPlanForm to save a new FPL in database
    form = FlightPlanForm(res)
    if form.is_valid():
        form.save()
    return render(request, "pages/index.html", {"data": json.dumps(res)})


@login_required
@require_http_methods(["POST"])
def submission(request: HttpRequest) -> JsonResponse:
    msg = request.POST.get(key="message", default=None)
    if not msg:
        return JsonResponse(
            {"error_message": "field message is missing", "error_code": "msg_not_found"}, status=400
        )
    if msg.startswith("(FPL"):
        return fpl_scrutinization(request, msg)
    return JsonResponse({"Error": "text must be an AFTN FPL message"}, status=400)


@staff_member_required
def export_models(request: HttpRequest) -> HttpResponse:
    """
    It exports the data of all models of this project to Excel files and returns
    a ZIP archive containing the Excel files as an HTTP response.
    """
    model_names = get_app_all_models("apps.")

    # Create a BytesIO object to store the ZIP archive
    zip_buffer = io.BytesIO()

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for model_name in model_names:
            excel_buffer = model_to_excel_bytesio(model_name)
            zip_file.writestr(f"{model_name}-{timestamp}.xlsx", excel_buffer.getvalue())

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
