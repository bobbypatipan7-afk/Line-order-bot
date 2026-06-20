from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

TH_TZ = timezone(timedelta(hours=7))


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        text = event.message.text.strip()

        if event.source.type != "group":
            return

        if len(text) < 2:
            return

        # ดึงชื่อ ถ้าไม่ได้ก็ใช้ค่าว่าง
        try:
            profile = line_bot_api.get_group_member_profile(
                event.source.group_id, event.source.user_id
            )
            sender_name = profile.display_name
        except Exception:
            sender_name = "สมาชิก"

        now = datetime.now(TH_TZ).strftime("%H:%M")

        reply = (
            f"รับทราบครับ ขอบคุณครับ\n"
            f"👤 {sender_name}\n"
            f"🕐 {now}\n"
            f"📋 {text}"
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )
    except Exception:
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
