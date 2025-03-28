import requests
import json
import jdatetime
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tokenbot import BASE_URL

def send_buttons(chat_id, permission):
    keyboard = []

    if permission <= 4:
        keyboard.append([
            {"text": "📌جلسات من     📌"  , "callback_data": "my joined"},
            {"text": "📌 کل جلسات    📌"  , "callback_data": "Meeting list"}
        ])

    if permission <= 4:
        keyboard.append([{"text": "افزودن یا ویرایش نام", "callback_data": "update_name"}])

    if permission <= 3:
        keyboard.append([
            {"text": "جلسات ایجاد شده", "callback_data": "my meet"},
            {"text": "تشکیل جلسه    📥", "callback_data": "create meeting"}
        ])

    if permission <= 3:
        keyboard.append([{"text": "لیست افراد قابل دعوت به جلسه", "callback_data": "all user list"}])

    if permission <=4 :
        keyboard.append([{"text": "راهنما", "callback_data": "help"}])
        
    reply_markup = {"inline_keyboard": keyboard}
    message_text = "لطفا یک دکمه را انتخاب کنید:"
    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "reply_markup": json.dumps(reply_markup)
    }
    response = requests.post(BASE_URL + 'sendMessage', json=payload)

def accept_meeting(chat_id):
    keyboard = [
        [{"text": "✅ تایید نهایی", "callback_data": "accept"}],
        [{"text": "🔙 بازگشت به لیست جلسات", "callback_data": "nonaccept"}]
    ]

    reply_markup = {"inline_keyboard": keyboard}
    message_text = "❓ آیا جلسه مورد تأیید است؟"
    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "reply_markup": json.dumps(reply_markup)
    }

    response = requests.post(BASE_URL + 'sendMessage', json=payload)

def send_participation_buttons(user_id, organizer_name, subject, meeting_id):
    message_text = (
        f"👤 شما توسط {organizer_name} به جلسه‌ای با عنوان «{subject}» دعوت شده‌اید.\n"
        "لطفاً حضور یا عدم حضور خود را اعلام بفرمایید."
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "✅ حضور دارم", "callback_data": f"join_{meeting_id}"}],
            [{"text": "❌ نمی‌توانم شرکت کنم", "callback_data": f"decline_{meeting_id}"}]
        ]
    }

    payload = {
        "chat_id": user_id,
        "text": message_text,
        "reply_markup": json.dumps(keyboard)
    }

    requests.post(BASE_URL + 'sendMessage', json=payload)


def send_my_meetings_with_cancel_button(chat_id, send_message):
    today = jdatetime.date.today().strftime('%Y-%m-%d')

    conn = sqlite3.connect("db.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, subject, date
        FROM meeting
        WHERE organizer = ? AND status = 1
    """, (chat_id,))
    all_meetings = cursor.fetchall()
    conn.close()

    # فقط جلساتی که تاریخشان امروز یا بعد است
    future_meetings = [m for m in all_meetings if m[2] >= today]

    if not future_meetings:
        send_message(chat_id, "📭 شما جلسه فعالی برای مدیریت ندارید.")
        return

    for m_id, subject, date in future_meetings:
        msg = f"📌 جلسه: {subject}\n📅 تاریخ: {date}"
        reply_markup = {
            "inline_keyboard": [
                [{"text": "❌ کنسل کردن جلسه", "callback_data": f"cancel_{m_id}"}]
            ]
        }
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "reply_markup": json.dumps(reply_markup)
        }
        requests.post(BASE_URL + 'sendMessage', json=payload)

def start(update, context):
    keyboard = [
        [InlineKeyboardButton("تاریخ امروز", callback_data='today')],
        [InlineKeyboardButton("فردا", callback_data='tomorrow')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('لطفا تاریخ را انتخاب کنید:', reply_markup=reply_markup)

def button(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    if data == 'today':
        # پردازش تاریخ امروز
        query.edit_message_text(text="تاریخ امروز انتخاب شد.")
    elif data == 'tomorrow':
        # پردازش تاریخ فردا
        query.edit_message_text(text="تاریخ فردا انتخاب شد.")