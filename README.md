# Sports2Calendar 赛事转播自动监控与日历同步

每天上午 10:00 自动检索以下赛事的转播计划并同步至 Google Calendar（**Sports_Live** 日历）与本地 iCalendar 文件：
1. **NBA** (Amazon Prime Video、CCTV-5)
2. **德国国家男子足球队** (ARD / Das Erste、ZDF、CCTV-5)
3. **UEFA Champions League 欧洲冠军联赛** (Amazon Prime Video 独家周二、ZDF 集锦/决赛、CCTV-5)
4. **欧洲五大联赛（英超、西甲、德甲、意甲、法甲）CCTV-5 / 央视体育转播信息**

## 监控平台

- **Amazon Prime Video** (德区独家欧冠周二焦点战、NBA Cup 黄金档及周五双重赛)
- **德国公共电视台免费频道** (ARD / Das Erste、ZDF 德国男足赛事、欧冠决赛及全景精华)
- **CCTV-5 / CCTV-5+ / 央视体育** (NBA、欧洲五大联赛实况直播与录像集锦)

## 核心配置与文件

- **目标日历**：Google Calendar `Sports_Live`
  - Calendar ID: `368d686b0d872d1813a5e5ed87a809ad0e4791fa32b54859f620deab5a31747d@group.calendar.google.com`
- `sports_sync.py`: 赛事同步工具，自动生成本地 `.ics` 并通过 `gcalendar` 直接推送到 Google Calendar 的 `Sports_Live` 日历中。
- `sports_schedule.ics`: 本地 iCalendar 格式文件（含开赛前 30 分钟提醒）。
- `events_data.json`: 本地去重数据库。
