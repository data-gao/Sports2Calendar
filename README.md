# Sports2Calendar

> Automated sports broadcast schedule tracking, iCalendar (.ics) generation, and Google Calendar sync.

Sports2Calendar aggregates live sports broadcast schedules across key platforms and leagues, maintains a deduplicated event database, exports standard iCalendar files, and synchronizes match events directly to Google Calendar with customizable reminders.

---

## 🏆 Supported Competitions & Channels

- **NBA**: Regular season & Emirates NBA Cup games (Amazon Prime Video, CCTV-5)
- **UEFA Champions League**: Tuesday marquee matches, official highlights, and finals (Amazon Prime Video DE, ZDF sportstudio, CCTV-5)
- **European Top Leagues**: Premier League, La Liga, Bundesliga, Serie A, Ligue 1 highlights & live broadcasts
- **National Team Tournaments**: UEFA Nations League, World Cup Qualifiers (ARD / Das Erste, ZDF)

### Monitored Platforms
- **Amazon Prime Video** (DE & International Prime sports coverage)
- **German Public Broadcasters** (ARD / Das Erste, ZDF sportstudio)
- **Sports Television Channels** (CCTV-5 / CCTV-5+ / CCTV Sports)

---

## 📦 Features

- **iCalendar (.ics) Export**: Generates RFC 5545 compliant `.ics` calendar files, compatible with Apple Calendar, Google Calendar, Outlook, and mobile devices.
- **Automated Alarms**: Configures pre-match alarm triggers (default 30 minutes before kickoff) for notifications.
- **Google Calendar Sync**: Integrates with Google Calendar (`gcalendar` CLI or API) to sync events seamlessly into designated calendars.
- **Deduplication Engine**: Uses cryptographic hashing (`MD5(title + start_time + broadcaster)`) to prevent duplicate entries across runs.
- **Desktop Alerts**: Triggers native desktop notifications on macOS / Linux upon scheduling new matches.

---

## 📁 Project Structure

```text
.
├── sports_sync.py        # Core CLI & synchronization tool
├── events_data.json      # Local deduplicated events database
├── sports_schedule.ics   # Exported standard iCalendar file
├── .env.example          # Environment configuration template
└── README.md             # Project documentation
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- (Optional) `gcalendar` CLI configured if syncing to Google Calendar.

### 2. Configuration

Copy `.env.example` to `.env` or set the environment variable:

```bash
cp .env.example .env
export GOOGLE_CALENDAR_ID="your-calendar-id@group.calendar.google.com"
```

> **Note**: If `GOOGLE_CALENDAR_ID` is omitted, it defaults to your `primary` Google Calendar.

### 3. Usage

#### List Scheduled Events
```bash
python3 sports_sync.py list
```

#### Add a New Match Event
```bash
python3 sports_sync.py add \
  "Germany vs. Netherlands" \
  "UEFA Nations League" \
  "ARD (Das Erste)" \
  "2026-11-20T20:45:00" \
  "2026-11-20T23:15:00" \
  "UEFA Nations League matchday fixture"
```

#### Re-export iCalendar (.ics)
```bash
python3 sports_sync.py export
```

---

## 🗓 Importing to Your Calendar

- **Apple Calendar / Outlook**: Double-click or open `sports_schedule.ics` to subscribe or import.
- **Google Calendar**: Go to Google Calendar Settings -> *Import & Export* -> Select `sports_schedule.ics` -> Choose target calendar -> *Import*.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
