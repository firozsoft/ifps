from django.forms import modelformset_factory
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from apps.models import *
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
        return JsonResponse({"error_message": "field message is missing", "error_code": "msg_not_found"})
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


import io
import json
import telegram
import pdf2image
# Initialize bot with webhook
bot = telegram.Bot(token='5947616037:AAHnsZTRkTSm5OhfLjo9SFuTZ4-fh9waW1Y')
bot.setWebhook(url='https://mhfzj.pythonanywhere.com/telegram')
from django.views.decorators.http import require_http_methods
@require_http_methods(["POST"])
def telegram_bot(request: HttpRequest):
    update = telegram.Update.de_json(json.loads(request.body), bot)

    # Check if message comes from my group
    if update.message.chat_id not in [378612331, -1001841304543]:
        return 'OK'

    # Check if message contains a PDF file
    if update.message.document and update.message.document.mime_type == 'application/pdf':

        pdf_name = update.message.document.file_name or "Untitled.pdf"
        caption = ''.join((update.message.caption or pdf_name).rsplit('.pdf', 1))

        # Download PDF file
        pdf_bytes = io.BytesIO(bot.getFile(update.message.document.file_id).download_as_bytearray())

        # Convert PDF to image
        pages = pdf2image.convert_from_bytes(pdf_bytes.read())

        if len(pages) == 0: return "OK"

        with io.BytesIO() as output:
            pages[0].save(output, format="JPEG")
            image_bytes = output.getvalue()

        # Send converted images back to group
        bot.send_photo(chat_id=update.message.chat_id, photo=image_bytes, caption=caption)

    return 'OK'
