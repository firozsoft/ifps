from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from fplcheck.analyses.logical_checks import logical_check
from fplcheck.analyses.regexer import regex_parse


def membership_status_check(user):
    return user.membership_status


# @login_required
# @user_passes_test(membership_status_check)
@require_http_methods(["POST"])
def scrutinization(request: HttpRequest) -> JsonResponse:
    msg = request.POST.get(key="message", default=None)
    if not msg:
        return JsonResponse(
            {"error_message": "field message is missing", "error_code": "msg_not_found"}
        )
    if msg.startswith("(FPL"):
        return fpl_scrutinization(msg)
    return JsonResponse({"Error": "text must be an AFTN FPL message"})


def fpl_scrutinization(msg: str) -> JsonResponse:
    parts = msg.split("-")
    field_data = {
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
    res, err = regex_parse(field_data)
    if err:
        return JsonResponse({"error_message": err.message, "error_code": err.code})
    err = logical_check(res)
    if err:
        return JsonResponse({"error_message": err.message, "error_code": err.code})
    return JsonResponse(res)
