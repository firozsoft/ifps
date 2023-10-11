import io
import logging

import pdf2image
import telegram
from flask import Flask, request

app = Flask(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize bot with webhook
bot = telegram.Bot(token="5947616037:AAHnsZTRkTSm5OhfLjo9SFuTZ4-fh9waW1Y")
bot.setWebhook(url="https://mhfzj.pythonanywhere.com/telegram")


@app.route("/telegram", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    logger.info(f"Received message from chat_id={update.message.chat_id}")

    # Check if message comes from my group
    if update.message.chat_id not in [378612331, -1001841304543]:
        return "OK"

    # Check if message contains a PDF file
    if (
        update.message.document
        and update.message.document.mime_type == "application/pdf"
    ):
        pdf_name = update.message.document.file_name or "Untitled.pdf"
        caption = "".join((update.message.caption or pdf_name).rsplit(".pdf", 1))

        # Download PDF file
        pdf_bytes = io.BytesIO(
            bot.getFile(update.message.document.file_id).download_as_bytearray()
        )

        # Convert PDF to image
        pages = pdf2image.convert_from_bytes(pdf_bytes.read())

        if len(pages) == 0:
            return "OK"

        with io.BytesIO() as output:
            pages[0].save(output, format="JPEG")
            image_bytes = output.getvalue()

        # Send converted images back to group
        bot.send_photo(
            chat_id=update.message.chat_id, photo=image_bytes, caption=caption
        )

    return "OK"
