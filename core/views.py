from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.serializers import serialize
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from core.analyzers import parser
from core.analyzers.integrity_analyzer import integrity_checks

FPL_EXPECTED_DASHES = 8


def user_has_subscription(user):
    return user.is_superuser or "Active" in user.userprofile.get_subscription_status()


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
