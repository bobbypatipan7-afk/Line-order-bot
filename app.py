from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from datetime import datetime
import subprocess

app = Flask(__name__)

# ===== ตั้งค่าตรงนี้ =====
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "ใส่ Channel Secret ของคุณ")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "ใส่ Channel Access Token ของคุณ")
PRINTER_NAME = os.environ.get("PRINTER_NAME", "")  # ชื่อ printer หรือเว้นว่างไว้ใช้ default
# ==========================

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

order_count = 0  # นับเลขออเดอร์


def print_order(sender_name, message, order_number):
    """สร้างใบออเดอร์และส่งปริ้น"""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    receipt = f"""
================================
       ใบออเดอร์ #{order_number}
================================
เวลา : {now}
ผู้สั่ง: {sender_name}
--------------------------------
{message}
--------------------------------
** กรุณาตรวจสอบก่อนทำอาหาร **
================================

"""

    # บันทึกเป็นไฟล์ชั่วคราวแล้วสั่งปริ้น
    tmp_file = f"/tmp/order_{order_number}.txt"
    with open(tmp_file, "w", encoding="utf-8") as f:
        f.write(receipt)

    # สั่งปริ้น (Linux/Raspberry Pi)
    if PRINTER_NAME:
        subprocess.run(["lp", "-d", PRINTER_NAME, tmp_file])
    else:
        subprocess.run(["lp", tmp_file])


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

    # ข้ามข้อความสั้นเกินไป (เช่น สติกเกอร์หรือแชททั่วไป)
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

    # เพิ่มเลขออเดอร์
    order_count += 1

    # ปริ้นออเดอร์
    print_order(sender_name, text, order_count)

    # ตอบกลับในกลุ่มให้รู้ว่ารับออเดอร์แล้ว
    reply = f"✅ รับออเดอร์ #{order_count} แล้วครับ!\n📋 {text}\n👤 {sender_name}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
