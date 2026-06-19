from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from datetime import datetime

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

order_count = 0


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
    global order_count

    text = event.message.text.strip()

    # รับเฉพาะข้อความจากกลุ่ม
    if event.source.type != "group":
        return

    # ข้ามข้อความสั้นเกินไป
    if len(text) < 3:
        return

    # ดึงชื่อผู้ส่ง
    try:
        profile = line_bot_api.get_group_member_profile(
            event.source.group_id, event.source.user_id
        )
        sender_name = profile.display_name
    except Exception:
        sender_name = "ไม่ทราบชื่อ"

    order_count += 1
    now = datetime.now().strftime("%H:%M")

    # ตอบกลับในกลุ่ม
    reply = (
        f"✅ รับออเดอร์ #{order_count} แล้วครับ!\n"
        f"👤 {sender_name}\n"
        f"🕐 {now}\n"
        f"📋 {text}"
    )
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
