import io
import json
import zipfile
from datetime import datetime

import pandas as pd
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.forms import model_to_dict
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from core.analyzers.logical_checks import logical_check
from core.analyzers.regexer import regex_parse
from core.utils.helpers import (
    field_value_normalize,
    get_app_all_models,
    get_model_class_and_fields,
)


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
    except Exception as exp:
        return JsonResponse({"internal_error": exp.__repr__()}, status=500)

    if err:
        return JsonResponse(err, status=400)

    try:
        err = logical_check(res)
    except Exception as exp:
        return JsonResponse({"internal_error": exp.__repr__()}, status=500)

    if err:
        return JsonResponse(err, status=400)

    return render(request, "pages/index.html", {"data": json.dumps(res)})


@login_required
@require_http_methods(["POST"])
def submission(request: HttpRequest) -> JsonResponse:
    msg = request.POST.get(key="message", default=None)
    if not msg:
        return JsonResponse({"error_message": "field message is missing", "error_code": "msg_not_found"})
    if msg.startswith("(FPL"):
        return fpl_scrutinization(request, msg)
    return JsonResponse({"Error": "text must be an AFTN FPL message"})


def model_to_excel_bytesio(model_name: str) -> io.BytesIO:
    # Get the model class and fields
    model_class, model_fields, expected_fields_for_excel, required_fields = get_model_class_and_fields(
        model_name
    )

    exportable_fields = [model_field.name for model_field in model_fields]

    # Retrieve data from the database
    # excel columns have to be field.verbose_name.upper and they'r values should be human readable
    # but model_to_dict dict is a key value pair of model field.name and field.value
    # the logic below is used to change dict key from field.name to field.verbose_name
    field_name_to_vbname = {
        model_field.name: model_field.verbose_name.upper() for model_field in model_fields
    }
    field_name_to_obj = {model_field.name: model_field for model_field in model_fields}
    data = [
        {
            field_name_to_vbname[field]: field_value_normalize(field_name_to_obj[field], value)
            for field, value in model_to_dict(instance, fields=exportable_fields).items()
        }
        for instance in model_class.objects.all()
    ]

    # Create a DataFrame from the data
    df = pd.DataFrame(data=data, columns=expected_fields_for_excel)

    # Create a BytesIO object to store the Excel file
    excel_buffer = io.BytesIO()

    # Write the DataFrame to the BytesIO object as an Excel file
    df.to_excel(excel_buffer, index=False)

    return excel_buffer


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
