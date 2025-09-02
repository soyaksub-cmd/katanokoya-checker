
import requests
import datetime
import icalendar
import smtplib
from email.mime.text import MIMEText

# GoogleカレンダーICSフィード（肩の小屋の予約状況）
ICS_URL = "https://calendar.google.com/calendar/ical/katanokoya3011@gmail.com/public/basic.ics"

# チェック対象日
TARGET_DATE = datetime.date(2025, 9, 27)

# Gmail設定（Secretsで渡すので、ここでは変数名だけ）
FROM_EMAIL = "your_gmail@gmail.com"
TO_EMAIL = "your_gmail@gmail.com"
APP_PASSWORD = "your_app_password"

def check_availability():
    data = requests.get(ICS_URL).content
    cal = icalendar.Calendar.from_ical(data)

    for comp in cal.walk():
        if comp.name == "VEVENT":
            start = comp.decoded("DTSTART").date()
            if start == TARGET_DATE:
                summary = str(comp.get("SUMMARY"))
                if summary in ("○", "△"):
                    return summary
    return None

def send_mail(status):
    msg = MIMEText(f"【肩の小屋】9/27の予約状況: {status}")
    msg["Subject"] = "肩の小屋 予約空きあり！"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(FROM_EMAIL, APP_PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    status = check_availability()
    if status:  # ○ or △ のときだけ通知
        send_mail(status)
