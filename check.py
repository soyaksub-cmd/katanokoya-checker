# check.py
import os
import datetime
import smtplib
from email.mime.text import MIMEText

import requests
import icalendar

ICS_URL = "https://calendar.google.com/calendar/ical/katanokoya3011@gmail.com/public/basic.ics"
_target_date_str = os.environ.get("TARGET_DATE", "2025-09-27")
TARGET_DATE = datetime.date.fromisoformat(_target_date_str)

AVAIL_MARKS = {"○": "空きあり", "△": "残りわずか"}
FULL_TOKENS = {"✕", "×", "X", "満室", "満了", "予約不可", "受付停止"}
MAIL_SUBJECT = f"肩の小屋 {TARGET_DATE:%-m/%-d} 空きあり！"


def fetch_calendar(ics_url: str) -> icalendar.Calendar:
    resp = requests.get(ics_url, timeout=30)
    resp.raise_for_status()
    return icalendar.Calendar.from_ical(resp.content)


def _to_date(value) -> datetime.date | None:
    """icalendar の DTSTART を date に正規化"""
    # icalendar の vDDDTypes は .dt を持つ場合がある
    if hasattr(value, "dt"):
        value = value.dt
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return None


def judge_status_for_date(cal: icalendar.Calendar, date_obj: datetime.date) -> str:
    status = None
    for comp in cal.walk():
        if comp.name != "VEVENT":
            continue

        start_raw = comp.get("DTSTART")
        if start_raw is None:
            continue
        start = _to_date(start_raw)
        if start is None:
            continue

        if start == date_obj:
            summary = str(comp.get("SUMMARY") or "").strip()

            for mark, label in AVAIL_MARKS.items():
                if mark in summary:
                    return label

            if any(tok in summary for tok in FULL_TOKENS):
                return "満室"

            status = f"不明: {summary}"  # 記号なし等
            # 同日複数イベントの可能性があるのでループは続行
    return status or "データなし"


def send_mail(body: str) -> None:
    FROM_EMAIL = os.environ["FROM_EMAIL"]
    TO_EMAIL = os.environ["TO_EMAIL"]
    APP_PASSWORD = os.environ["APP_PASSWORD"]

    msg = MIMEText(body)
    msg["Subject"] = MAIL_SUBJECT
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.starttls()
        server.login(FROM_EMAIL, APP_PASSWORD)
        server.send_message(msg)


def main() -> int:
    try:
        cal = fetch_calendar(ICS_URL)
    except Exception as e:
        print(f"ICS取得失敗: {e}")
        return 0  # 取得失敗でも通知しない運用

    status = judge_status_for_date(cal, TARGET_DATE)

    if status in AVAIL_MARKS.values():
        body = f"【肩の小屋】{TARGET_DATE:%-m/%-d} の予約状況: {status}\n（このメールが来たら即・電話推奨）"
        try:
            send_mail(body)
            print(f"通知送信: {status}")
        except Exception as e:
            print(f"メール送信失敗: {e}")
    else:
        print(f"通知なし: {status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
