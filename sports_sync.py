#!/usr/bin/env python3
"""
Sports2Calendar - Sports Broadcast to iCalendar & Google Calendar Sync Tool
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
        dt = datetime.datetime.strptime(dt_str[:16], "%Y-%m-%dT%H:%M")
    return dt.strftime("%Y%m%dT%H%M%S")

def export_ics(events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Sports2Calendar//Sports Schedule//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Sports Broadcast Schedule",
        "X-WR-TIMEZONE:Europe/Berlin"
    ]

    now_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for ev in events:
        uid = ev.get("uid") or generate_uid(ev["title"], ev["start_time"], ev["broadcaster"])
        start_ics = format_ics_date(ev["start_time"])
        end_ics = format_ics_date(ev.get("end_time") or ev["start_time"])
        
        summary = f"[{ev['broadcaster']}] {ev['title']}"
        desc = f"Competition: {ev.get('competition', '')}\\nBroadcaster: {ev['broadcaster']}\\nDetails: {ev.get('details', '')}"

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
            f"DESCRIPTION:Match Reminder: {summary}",
            "END:VALARM",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines) + "\r\n")

def send_notification(title, message):
    # Desktop notification fallback (macOS osascript)
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def sync_to_google_calendar(ev):
    calendar_id = os.environ.get("GOOGLE_CALENDAR_ID", "primary")
    summary = f"[{ev['broadcaster']}] {ev['title']}"
    desc = f"Competition: {ev.get('competition', '')}\nBroadcaster: {ev['broadcaster']}\nDetails: {ev.get('details', '')}"
    
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
            print(f"[GOOGLE CALENDAR] Successfully synced: {summary}")
        else:
            # If specified calendar fails and was not primary, fallback to primary
            if calendar_id != "primary":
                cal_idx = cmd.index("--cal")
                cmd[cal_idx + 1] = "primary"
                res_primary = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if res_primary.returncode == 0:
                    print(f"[GOOGLE CALENDAR] Successfully synced (Primary): {summary}")
                    return
            print(f"[GOOGLE CALENDAR] Sync error: {res.stderr or res.stdout}")
    except Exception as e:
        print(f"[GOOGLE CALENDAR] Exception: {e}")

def add_event(title, competition, broadcaster, start_time, end_time="", details=""):
    events = load_events()
    uid = generate_uid(title, start_time, broadcaster)
    
    # Check if already exists
    for ev in events:
        if ev.get("uid") == uid:
            print(f"[EXISTS] Event already scheduled: {title} ({broadcaster})")
            return False

    if not end_time:
        # Default duration: 2.5 hours
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
    print(f"[ADDED] Successfully added event: {title} | Broadcaster: {broadcaster} | Time: {start_time}")
    send_notification("New Sports Broadcast Reminder", f"[{broadcaster}] {title} ({start_time})")
    sync_to_google_calendar(new_ev)
    return True

def list_events():
    events = load_events()
    if not events:
        print("No scheduled sports events found.")
        return
    print(f"Total scheduled events: {len(events)}")
    for i, ev in enumerate(events, 1):
        print(f"{i}. [{ev['broadcaster']}] {ev['title']} ({ev.get('competition', '')}) - {ev['start_time']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 sports_sync.py list")
        print("  python3 sports_sync.py add <title> <competition> <broadcaster> <start_time> [end_time] [details]")
        print("  python3 sports_sync.py export")
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
        print(f"Exported to {CALENDAR_FILE}")
    else:
        print(f"Unknown command: {cmd}")
