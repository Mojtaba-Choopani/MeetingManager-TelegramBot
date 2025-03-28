# Meeting Manager Telegram Bot (Full Source)

A Persian-language Telegram bot for managing meetings and participant invitations with fuzzy name matching, automated scheduling, and smart reminders.

---

## 🚀 Features

- 🗓️ Create, manage, and cancel meetings
- 👥 Invite participants by name (fuzzy matching supported)
- 🕒 Time conflict detection
- 📆 Full Shamsi (Jalali) date support using `jdatetime`
- 🔔 Automatic daily reminders at 6 AM
- 🔐 Role-based permissions (Organizer, Participant)
- 💬 Fully localized Persian UX

---

## 🛠️ Tech Stack

- Python 3
- Telegram Bot API (`python-telegram-bot`)
- SQLite3
- jdatetime (Shamsi support)
- fuzzywuzzy (name matching)
- dateparser

---

## 📦 Installation

```bash
git clone https://github.com/yourusername/MeetingManager-FullBot.git
cd MeetingManager-FullBot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
