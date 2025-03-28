from meeting_creator import handle_meeting_creation, user_states, save_meeting
from send_update import send_message, get_updates
from data_base import update_or_create_user, send_meeting_list, get_user_name
from data_base import check_user_name_exists, update_user_field, get_user_permission
from data_base import append_participant_to_meeting, send_high_permission_users
from buttons import send_buttons, accept_meeting, send_participation_buttons
from buttons import send_my_meetings_with_cancel_button
from data_base import cancel_meeting_by_organizer, send_user_meetings
from reminder_bot import send_today_meeting_reminders
import time
import datetime
from zoneinfo import ZoneInfo


reminder_sent = False

def handle_message(update):
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        message = update['message']['text']

        # مرحله ساخت جلسه اگر فعال باشد
        if chat_id in user_states and isinstance(user_states[chat_id], dict) and 'step' in user_states[chat_id]:
            handle_meeting_creation(chat_id, message, send_message, accept_meeting)
            return

        if message == '/start':
            send_message(chat_id, 
                "سلام! 👋\n"
                "به بات مدیریت جلسات خوش آمدید.\n\n"
                "این بات توسط آقای چوپانی توسعه داده شده است.\n"
                "در صورت وجود باگ یا داشتن پیشنهاد، لطفاً در پیام خصوصی به آدرس زیر اطلاع دهید:\n"
                "@choopanii"
            )
            update_or_create_user(chat_id, message)
            send_buttons(chat_id, get_user_permission(chat_id))
            return

        if (check_user_name_exists(chat_id) == 0 and 
            message not in (None, '/start', '') and
            user_states.get(chat_id) is None):

            send_message(chat_id, "لطفاً برای برنامه‌ریزی جلسات آینده،"
            " نام و نام خانوادگی خود را از طریق کلید"
            " 'افزودن یا ویرایش نام' وارد کنید.")
            send_buttons(chat_id, get_user_permission(chat_id))
            return

        if user_states.get(chat_id) == "waiting_for_name":
            update_user_field(chat_id, 'name', message)
            send_message(chat_id, "نام شما با موفقیت ثبت گردید")
            send_buttons(chat_id, get_user_permission(chat_id))
            user_states[chat_id] = None
            return
    send_buttons(chat_id, get_user_permission(chat_id))


def handle_callback(update):

    query = update['callback_query']
    data = query['data']
    chat_id = query['from']['id']
    if (check_user_name_exists(chat_id) == 0 and
        data != 'update_name') :
        send_message(chat_id, "لطفاً برای برنامه‌ریزی جلسات آینده،"
        " نام و نام خانوادگی خود را از طریق کلید"
        " 'افزودن یا ویرایش نام' وارد کنید.")
        send_buttons(chat_id, get_user_permission(chat_id))
        return 
    
    if data == 'update_name':
        user_states[chat_id] = "waiting_for_name"
        send_message(chat_id, "لطفاً نام و نام خانوادگی خود را وارد کنید.")
        return

    if data == 'Meeting list':
        user_states[chat_id] = "meeting list"
        send_message(chat_id, "در حال نمایش لیست جلسات...")
        send_meeting_list(chat_id)
        send_buttons(chat_id, get_user_permission(chat_id))
        return
    
    if data == 'all user list':
        user_states[chat_id] = "all user list"
        send_high_permission_users(chat_id)
        send_buttons(chat_id, get_user_permission(chat_id))
        return

    if data == 'create meeting':
        user_states[chat_id] = {"step": "awaiting_subject"}
        send_message(chat_id, "📝 لطفاً عنوان جلسه را وارد کنید:")
        return

    if data == 'accept':
        if chat_id in user_states and isinstance(user_states[chat_id], dict):
            state = user_states[chat_id]
            if state.get('step') == 'awaiting_confirmation':
                meeting_id = save_meeting({
                    'subject': state['subject'],
                    'date': state['date'],
                    'start_hour': state['start_hour'],
                    'end_hour': state['end_hour'],
                    'organizer': chat_id
                })

                for uid in state['participant_ids']:
                    send_participation_buttons(
                        user_id=uid,
                        organizer_name=get_user_name(chat_id),
                        subject=state['subject'],
                        meeting_id=meeting_id
                    )

                send_message(chat_id, "✅ جلسه با موفقیت ثبت شد و دعوت‌نامه‌ها ارسال شدند.")
                user_states.pop(chat_id)
                send_buttons(chat_id, get_user_permission(chat_id))
                return

    if data.startswith("join_"):
        meeting_id = int(data.split("_")[1])
        append_participant_to_meeting(chat_id, meeting_id)
        send_message(chat_id, "✅ حضور شما در جلسه ثبت شد.")
        send_buttons(chat_id, get_user_permission(chat_id))
        return

    if data.startswith("decline_"):
        send_message(chat_id, "❌ عدم حضور شما در جلسه ثبت شد.")
        send_buttons(chat_id, get_user_permission(chat_id))
        return
    
    if data == 'my meet':
        send_my_meetings_with_cancel_button(chat_id,send_message)
        send_buttons(chat_id, get_user_permission(chat_id))
        return
    
    if data.startswith("cancel_"):
        meeting_id = int(data.split("_")[1])
        msg = cancel_meeting_by_organizer(meeting_id, chat_id)
        send_message(chat_id, msg)
        send_buttons(chat_id, get_user_permission(chat_id))
        return
    
    if data == 'my joined' :
        send_user_meetings(chat_id)
        send_buttons(chat_id, get_user_permission(chat_id))
        return

    if data == 'help' :
        help_text = (
        "📘 راهنمای استفاده از ربات مدیریت جلسات:\n\n"
        "🔹 افزودن یا ویرایش نام: ابتدا نام خود را ثبت کنید.\n"
        "🔹 تشکیل جلسه جدید: جلسه‌ای با عنوان، تاریخ، ساعت و اعضا ایجاد کنید.\n"
        "🔹 لیست کل جلسات: مشاهده جلسات فعال (در صورت داشتن دسترسی).\n"
        "🔹 جلسات من: جلساتی که خودتان ایجاد کرده‌اید را ببینید و مدیریت کنید.\n"
        "🔹 دعوت‌شده‌ام: جلساتی که در آن‌ها دعوت شده‌اید را مشاهده کنید.\n"
        "🔹 اطلاع‌رسانی خودکار: روزانه ساعت ۶ صبح برای اعضای جلسات امروز پیام یادآوری ارسال می‌شود.\n\n"
        "✅ پس از تشکیل جلسه، فقط اعضایی که تایید کنند در جلسه ثبت خواهند شد."
        )
        send_message(chat_id, help_text)
        send_buttons(chat_id, get_user_permission(chat_id))
        return

def main():
    global reminder_sent
    last_update_id = None
    while True:
        tehran_now = datetime.datetime.now(ZoneInfo("Asia/Tehran"))

        # اجرای یادآوری جلسات رأس ساعت ۶ صبح
        if tehran_now.hour == 6 and not reminder_sent:
            send_today_meeting_reminders()
            reminder_sent = True

        if tehran_now.hour > 6:
            reminder_sent = False

        updates = get_updates(last_update_id)
        if updates:
            for update in updates:
                if 'callback_query' in update:
                    handle_callback(update)
                elif 'message' in update:
                    handle_message(update)
                last_update_id = update['update_id'] + 1

        time.sleep(1)

if __name__ == '__main__':
    main()
