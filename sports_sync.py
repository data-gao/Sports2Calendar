#!/usr/bin/env python3
"""
Sports2Calendar - Sports Broadcast to iCalendar & Notification Sync Tool
"""

import sys
import json
import os
import datetime
import hashlib
import subprocess

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
CALENDAR_FILE = os.path.join(WORKSPACE_DIR, "sports_schedule.ics")
DATA_FILE = os.path.join(WORKSPACE_DIR, "events_data.json")

def load_events():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_events(events):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def generate_uid(title, start_time, broadcaster):
    raw = f"{title}_{start_time}_{broadcaster}".encode("utf-8")
    return hashlib.md5(raw).hexdigest() + "@sports2calendar"

def format_ics_date(dt_str):
    # Expects ISO format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD HH:MM
    dt_str = dt_str.replace(" ", "T")
    try:
        dt = datetime.datetime.fromisoformat(dt_str)
    except Exception:
        # Fallback if no seconds
        dt = datetime.datetime.strptime(dt_str[:16], "%Y-%m-%dT%H:%M")
    return dt.strftime("%Y%m%dT%H%M%S")

def export_ics(events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Antigravity//Sports2Calendar//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:体育赛事转播日程",
        "X-WR-TIMEZONE:Europe/Berlin"
    ]

    now_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for ev in events:
        uid = ev.get("uid") or generate_uid(ev["title"], ev["start_time"], ev["broadcaster"])
        start_ics = format_ics_date(ev["start_time"])
        end_ics = format_ics_date(ev.get("end_time") or ev["start_time"])
        
        summary = f"[{ev['broadcaster']}] {ev['title']}"
        desc = f"赛事: {ev.get('competition', '')}\\n转播平台: {ev['broadcaster']}\\n详情: {ev.get('details', '')}"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{start_ics}",
            f"DTEND:{end_ics}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            f"LOCATION:{ev['broadcaster']}",
            "STATUS:CONFIRMED",
            "BEGIN:VALARM",
            "TRIGGER:-PT30M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:赛事开赛提醒: {summary}",
            "END:VALARM",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines) + "\r\n")

def send_notification(title, message):
    # Try AppleScript notification if outside sandbox
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def sync_to_google_calendar(ev):
    calendar_id = "368d686b0d872d1813a5e5ed87a809ad0e4791fa32b54859f620deab5a31747d@group.calendar.google.com"
    summary = f"[{ev['broadcaster']}] {ev['title']}"
    desc = f"赛事: {ev.get('competition', '')}\n转播平台: {ev['broadcaster']}\n详情: {ev.get('details', '')}"
    
    # Format RFC3339 with timezone offset
    st = ev['start_time'].replace(" ", "T")
    if "+" not in st and not st.endswith("Z"):
        st += "+01:00"
    et = ev['end_time'].replace(" ", "T")
    if "+" not in et and not et.endswith("Z"):
        et += "+01:00"

    cmd = [
        "gcalendar", "mutate", "create",
        "--cal", calendar_id,
        "--summary", summary,
        "--start", st,
        "--end", et,
        "--location", ev['broadcaster'],
        "--description", desc,
        "--transparency", "transparent"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            print(f"[GOOGLE CALENDAR] 同步成功: {summary}")
        else:
            # If failed, try primary calendar
            cal_idx = cmd.index("--cal")
            cmd[cal_idx + 1] = "primary"
            res_primary = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res_primary.returncode == 0:
                print(f"[GOOGLE CALENDAR] 同步成功 (Primary): {summary}")
            else:
                print(f"[GOOGLE CALENDAR] 同步错误: {res.stderr or res.stdout}")
    except Exception as e:
        print(f"[GOOGLE CALENDAR] 异常: {e}")

def add_event(title, competition, broadcaster, start_time, end_time="", details=""):
    events = load_events()
    uid = generate_uid(title, start_time, broadcaster)
    
    # Check if already exists
    for ev in events:
        if ev.get("uid") == uid:
            print(f"[EXISTS] 比赛已在日程中: {title} ({broadcaster})")
            return False

    if not end_time:
        # Default duration 2.5 hours
        try:
            st = datetime.datetime.fromisoformat(start_time.replace(" ", "T"))
            et = st + datetime.timedelta(hours=2.5)
            end_time = et.strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            end_time = start_time

    new_ev = {
        "uid": uid,
        "title": title,
        "competition": competition,
        "broadcaster": broadcaster,
        "start_time": start_time,
        "end_time": end_time,
        "details": details,
        "created_at": datetime.datetime.now().isoformat()
    }
    events.append(new_ev)
    save_events(events)
    export_ics(events)
    print(f"[ADDED] 成功添加赛事日程: {title} | 转播: {broadcaster} | 时间: {start_time}")
    send_notification("新赛事转播提醒", f"[{broadcaster}] {title} ({start_time})")
    sync_to_google_calendar(new_ev)
    return True

def list_events():
    events = load_events()
    if not events:
        print("当前没有任何已记录的赛事日程。")
        return
    print(f"当前共记录 {len(events)} 场比赛:")
    for i, ev in enumerate(events, 1):
        print(f"{i}. [{ev['broadcaster']}] {ev['title']} ({ev.get('competition', '')}) - {ev['start_time']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 sports_sync.py list")
        print("  python3 sports_sync.py add <title> <competition> <broadcaster> <start_time> [end_time] [details]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        list_events()
    elif cmd == "add":
        if len(sys.argv) < 6:
            print("Usage: python3 sports_sync.py add <title> <competition> <broadcaster> <start_time> [end_time] [details]")
            sys.exit(1)
        title = sys.argv[2]
        comp = sys.argv[3]
        broadcaster = sys.argv[4]
        start = sys.argv[5]
        end = sys.argv[6] if len(sys.argv) > 6 else ""
        details = sys.argv[7] if len(sys.argv) > 7 else ""
        add_event(title, comp, broadcaster, start, end, details)
    elif cmd == "export":
        events = load_events()
        export_ics(events)
        print(f"已导出到 {CALENDAR_FILE}")
    else:
        print(f"Unknown command: {cmd}")
