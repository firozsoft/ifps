import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from core.analyzers.logical_checks import logical_check  # noqa
from core.analyzers.regexer import regex_parse


def membership_status_check(user):
    return user.membership_status


@login_required
@require_http_methods(["POST"])
def scrutinization(request: HttpRequest) -> JsonResponse:
    msg = request.POST.get(key="message", default=None)
    if not msg:
        return JsonResponse({"error_message": "field message is missing", "error_code": "msg_not_found"})
    if msg.startswith("(FPL"):
        return fpl_scrutinization(request, msg)
    return JsonResponse({"Error": "text must be an AFTN FPL message"})


def fpl_scrutinization(request, msg: str) -> JsonResponse:
    parts = list(map(str.strip, msg.split("-")))
    filled_data = {
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

    res, err = regex_parse(filled_data)
    if err:
        return JsonResponse(err.params)
    err = logical_check(res)
    if err:
        # return render(request, "index.html", {"data": json.dumps(err.params)})
        return JsonResponse(err.params)
    return render(request, "index.html", {"data": json.dumps(res)})
