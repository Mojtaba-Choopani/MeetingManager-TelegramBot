
import sqlite3
import jdatetime
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from tokenbot import BASE_URL


def send_message(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(BASE_URL + "sendMessage", json=payload)

def get_user_name(user_id):
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else f"ناشناس({user_id})"

def send_today_meeting_reminders():
    tehran_now = datetime.now(ZoneInfo("Asia/Tehran"))
    today_shamsi = jdatetime.date.fromgregorian(date=tehran_now.date()).strftime('%Y-%m-%d')

    conn = sqlite3.connect("db.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subject, date, `start hour`, `end hour`, organizer, participats
        FROM meeting
        WHERE status = 1 AND date = ?
    """, (today_shamsi,))
    meetings = cursor.fetchall()
    conn.close()

    for subject, date, start, end, organizer, participats in meetings:
        organizer_name = get_user_name(organizer)
        participant_ids = participats.split('-') if participats else []

        message = (
            f"⏰ یادآوری جلسه امروز:\n"
            f"• عنوان: {subject}\n"
            f"• تاریخ: {date}\n"
            f"• ساعت: {start} تا {end}\n"
            f"• تشکیل‌دهنده: {organizer_name}\n"
        )

        for uid in participant_ids:
            if uid.strip().isdigit():
                send_message(int(uid), message)