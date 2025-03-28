import sqlite3
from fuzzywuzzy import process
import jdatetime
import dateparser
from datetime import datetime
user_states = {}  # وضعیت مرحله‌ای کاربران

def get_today_shamsi():
    return jdatetime.date.today().strftime('%Y-%m-%d')

def get_user_name(user_id):
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else f"ناشناس({user_id})"

def get_all_users():
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name FROM users WHERE name IS NOT NULL")
    result = cursor.fetchall()
    conn.close()
    return result

def match_participants(typed_names, db_users, threshold=70):
    db_names = [name for _, name in db_users]
    matched = []
    errors = []

    for typed in typed_names:
        best_match, score = process.extractOne(typed, db_names)
        if score >= threshold:
            user_id = next(uid for uid, name in db_users if name == best_match)
            matched.append((typed, best_match, user_id))
        else:
            errors.append(typed)
    return matched, errors

def check_schedule_conflicts(user_ids, date, start_hour, end_hour):
    conn = sqlite3.connect("db.db")
    cursor = conn.cursor()
    conflicts = []

    for uid in user_ids:
        cursor.execute("""
        SELECT subject, date, `start hour`, `end hour`, organizer
        FROM meeting
        WHERE participats LIKE ? AND date = ? AND status = 1
        """, (f"%{uid}%", date))
        sessions = cursor.fetchall()
        for sub, d, s_start, s_end, org_id in sessions:
            if not (end_hour <= s_start or start_hour >= s_end):
                org_name = get_user_name(org_id)
                conflicts.append((uid, sub, s_start, s_end, org_name))
    conn.close()
    return conflicts

def save_meeting(data):
    conn = sqlite3.connect("db.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO meeting (subject, date, `start hour`, `end hour`, organizer, participats, status)
        VALUES (?, ?, ?, ?, ?, NULL, 1)
    """, (
        data['subject'],
        data['date'],
        data['start_hour'],
        data['end_hour'],
        data['organizer']
    ))
    meeting_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return meeting_id

def generate_summary(data):
    names = [get_user_name(uid) for uid in data['participant_ids']]
    return (
        f"\U0001F4C4 خلاصه جلسه:\n"
        f"عنوان: {data['subject']}\n"
        f"تاریخ: {data['date']}\n"
        f"ساعت: {data['start_hour']} تا {data['end_hour']}\n"
        f"تشکیل‌دهنده: {get_user_name(data['organizer'])}\n"
        f"اعضا: {', '.join(names)}"
    )

def handle_meeting_creation(chat_id, message, send_message, accept_meeting):
    state = user_states.get(chat_id)
    if not state:
        return

    step = state['step']

    if step == 'awaiting_subject':
        state['subject'] = message  # فرض بر اینکه message دارای ویژگی text است
        state['step'] = 'awaiting_date'
        send_message(chat_id, "\U0001F4C5 لطفاً تاریخ جلسه را وارد کنید (مثلاً: 02-12-1404):")
   
    elif step == 'awaiting_date':
        # استفاده از dateparser برای تجزیه تاریخ
        datetime_obj = dateparser.parse(message)
        if datetime_obj:
            state['date'] = datetime_obj.strftime('%Y-%m-%d')  # فرمت‌بندی تاریخ به صورت استاندارد
            state['step'] = 'awaiting_start_hour'
            send_message(chat_id, "⏰ ساعت شروع جلسه را وارد کنید (مثلاً: 14:30):")
        else:
            send_message(chat_id, "لطفاً یک تاریخ معتبر وارد کنید (مثلاً: 02-12-1404):")

    elif step == 'awaiting_start_hour':
        try:
            datetime.strptime(message, '%H:%M')
            state['start_hour'] = message
            state['step'] = 'awaiting_end_hour'
            send_message(chat_id, "⏳ ساعت پایان جلسه را وارد کنید (مثلاً: 15:30):")
        except ValueError:
            send_message(chat_id, "❌ لطفاً یک ساعت معتبر  (حتما به انگلیسی) وارد کنید به فرمت HH:MM (مثلاً: 14:30)")

    elif step == 'awaiting_end_hour':
        try:
            datetime.strptime(message, '%H:%M')
            state['end_hour'] = message
            state['step'] = 'awaiting_participants'
            send_message(chat_id, "👥 لطفاً نام اعضای جلسه را با - جدا کنید (مثلاً: علی رضایی - زهرا محمدی):")
        except ValueError:
            send_message(chat_id, "❌ لطفاً یک ساعت معتبر (حتما به انگلیسی) وارد کنید به فرمت HH:MM (مثلاً: 15:30)")
        
    elif step == 'awaiting_participants':
        typed_names = [name.strip() for name in message.split('-')]
        db_users = get_all_users()
        matched, errors = match_participants(typed_names, db_users)

        if errors:
            send_message(chat_id, f"❌ نام‌های زیر یافت نشدند یا شباهت کافی نداشتند:\n" + "\n".join(errors))
            return

        participant_ids = [uid for _, _, uid in matched]
        conflicts = check_schedule_conflicts(participant_ids, state['date'], state['start_hour'], state['end_hour'])

        if conflicts:
            text = "⚠️ تداخل زمانی برای اعضای زیر وجود دارد:\n"
            for uid, sub, start, end, org in conflicts:
                text += f"- {get_user_name(uid)} در جلسه «{sub}» از {start} تا {end} ایجاد شده توسط {org}\n"
            send_message(chat_id, text)
            return

        state['participant_ids'] = participant_ids
        state['step'] = 'awaiting_confirmation'

        summary = generate_summary({
            'subject': state['subject'],
            'date': state['date'],
            'start_hour': state['start_hour'],
            'end_hour': state['end_hour'],
            'organizer': chat_id,
            'participant_ids': participant_ids
        })

        send_message(chat_id, summary + "\n\n👇 اگر اطلاعات درست است، روی دکمه زیر کلیک کنید:")
        accept_meeting(chat_id)