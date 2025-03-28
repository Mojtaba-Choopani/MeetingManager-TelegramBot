import sqlite3
import jdatetime
from send_update import send_message

def connect_to_db():
    return sqlite3.connect('db.db')

def update_or_create_user(chat_id, text):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # بررسی اینکه آیا کاربر در دیتابیس وجود دارد
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (chat_id,))
    user = cursor.fetchone()
    
    if user:
        # کاربر وجود دارد، پس فقط last_message را به‌روزرسانی کن
        cursor.execute('UPDATE users SET last_message = ? WHERE user_id = ?', (text, chat_id))
    else:
        # کاربر وجود ندارد، پس یک رکورد جدید ایجاد کن
        cursor.execute('INSERT INTO users (user_id, last_message, permission) VALUES (?, ?, ?)', 
                       (chat_id, text, 4))
    
    # ذخیره تغییرات و بستن اتصال دیتابیس
    conn.commit()
    conn.close()

def check_user_name_exists(user_id):
    # اتصال به دیتابیس
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    
    # بررسی وجود نام کاربر
    cursor.execute('SELECT name FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    # بستن اتصال دیتابیس
    conn.close()
    
    # بررسی و برگرداندن نتیجه
    if result and result[0] and result[0].strip():
        return 1  # نام کاربر موجود و معتبر است
    else:
        return 0  # نام کاربر موجود نیست یا خالی است

def update_user_field(user_id, field_name, new_value):
    # فیلدهای مجاز برای بروزرسانی را تعریف می‌کنیم
    allowed_fields = ['name', 'last_message', 'permission']

    # بررسی امنیتی برای اطمینان از اینکه نام فیلد مجاز است
    if field_name not in allowed_fields:
        raise ValueError(f"Field name '{field_name}' is not allowed.")

    # اتصال به دیتابیس
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # ساخت کوئری SQL و اجرای آن
    query = f'UPDATE users SET {field_name} = ? WHERE user_id = ?'
    cursor.execute(query, (new_value, user_id))
    
    # ذخیره تغییرات
    conn.commit()
    
    # بستن اتصال دیتابیس
    conn.close()

def get_user_permission(user_id):
    # اتصال به دیتابیس
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # اجرای کوئری برای یافتن سطح دسترسی کاربر
    cursor.execute("SELECT permission FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    # بستن اتصال دیتابیس
    conn.close()
    
    # بررسی نتیجه و برگرداندن سطح دسترسی
    if result:
        return result[0]  # برگرداندن سطح دسترسی
    else:
        return None  # در صورت نیافتن کاربر، None برگرداند

def get_today_shamsi(): # دریافت تاریخ روز
    today = jdatetime.date.today()
    return today.strftime('%Y-%m-%d')  # خروجی مثل 1403-01-23

def get_future_meetings():
    today = get_today_shamsi()
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    #  و satus=1 گرفتن جلسات با تاریخ امروز یا بعد از آن
    cursor.execute("SELECT id, subject, date, `start hour`, `end hour`, organizer, participats FROM meeting WHERE date >= ? AND status = 1", (today,))
    meetings = cursor.fetchall()
    conn.close()
    return meetings

def get_user_name(user_id): #convert user id
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else f"ناشناس({user_id})"

def format_meeting_info(meeting): 
    id, subject, date, start_hour, end_hour, organizer_id, participants_str = meeting

    # گرفتن نام برگزارکننده
    organizer_name = get_user_name(organizer_id)

    # گرفتن نام اعضا
    if participants_str:
        participant_ids = participants_str.split('-')
    else:
        participant_ids = []
    participant_names = [get_user_name(int(pid)) for pid in participant_ids]

    text = (
        f"📝 عنوان جلسه: {subject}\n"
        f"📅 تاریخ: {date}\n"
        f"👤 تشکیل‌دهنده: {organizer_name}\n"
        f"⏰ ساعت: {start_hour} تا {end_hour}\n"
        f"👥 اعضا: {', '.join(participant_names)}\n"
        "-------------------------"
    )
    return text

def send_meeting_list(chat_id):
    meetings = get_future_meetings()

    if not meetings:
        send_message(chat_id, "هیچ جلسه‌ای برای امروز یا آینده ثبت نشده است.")
        return

    for meeting in meetings:
        text = format_meeting_info(meeting)
        send_message(chat_id, text)

def append_participant_to_meeting(user_id, meeting_id):
    conn = sqlite3.connect("db.db")
    cursor = conn.cursor()
    cursor.execute("SELECT participats FROM meeting WHERE id = ?", (meeting_id,))
    current = cursor.fetchone()[0]

    if current:
        updated = current + "-" + str(user_id)
    else:
        updated = str(user_id)

    cursor.execute("UPDATE meeting SET participats = ? WHERE id = ?", (updated, meeting_id))
    conn.commit()
    conn.close()

def send_high_permission_users(chat_id):
    conn = sqlite3.connect("db.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, user_id, permission FROM users WHERE permission > 1")
    users = cursor.fetchall()
    conn.close()

    if not users:
        send_message(chat_id, "کاربری با سطح دسترسی بالاتر از ۱ یافت نشد.")
        return

    msg = "👤 لیست اسامی قابل انتخاب جهت دعوت به جلسه:\n"
    for name, user_id, perm in users:
        display_name = name if name else f"کاربر {user_id}"
        msg += f"▫️ {display_name}\n"

    send_message(chat_id, msg)

def cancel_meeting_by_organizer(meeting_id, chat_id):
    conn = sqlite3.connect("db.db")
    cursor = conn.cursor()

    # بررسی اینکه جلسه وجود دارد و مربوط به همین کاربر است
    cursor.execute("SELECT subject FROM meeting WHERE id = ? AND organizer = ?", (meeting_id, chat_id))
    row = cursor.fetchone()

    if row:
        subject = row[0]
        cursor.execute("UPDATE meeting SET status = 0 WHERE id = ?", (meeting_id,))
        conn.commit()
        conn.close()
        return f"❌ جلسه «{subject}» با موفقیت کنسل شد."
    else:
        conn.close()
        return "❗ جلسه‌ای با این شناسه یافت نشد یا شما برگزارکننده آن نیستید."
    
import sqlite3

def send_user_meetings(chat_id):
    today = jdatetime.date.today().strftime('%Y-%m-%d')

    conn = sqlite3.connect("db.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subject, date, `start hour`, `end hour`, organizer
        FROM meeting
        WHERE status = 1 AND participats LIKE ?
    """, (f"%{chat_id}%",))
    all_meetings = cursor.fetchall()
    conn.close()

    # فقط جلسات امروز یا بعد
    meetings = [m for m in all_meetings if m[1] >= today]

    if not meetings:
        send_message(chat_id, "📭 شما در هیچ جلسه آینده‌ای ثبت‌نام نشده‌اید.")
        return

    msg = "📅 جلساتی که در آن‌ها شرکت دارید:\n\n"
    for subject, date, start, end, org in meetings:
        org_name = get_user_name(org)
        msg += (
            f"• عنوان: {subject}\n"
            f"  تاریخ: {date}\n"
            f"  ساعت: {start} تا {end}\n"
            f"  تشکیل‌دهنده: {org_name}\n\n"
        )

    send_message(chat_id, msg)