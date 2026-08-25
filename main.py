from datetime import datetime, date, timedelta
import chinese_calendar
import holidays
from icalendar import Calendar, Event
import os

# ========== Configuration ==========
YEAR = 2026
OUTPUT_DIR = "output"

CN_HOLIDAY_CAT = 'Red category'    # China holidays -> Red
CN_WORK_CAT = 'Orange category'    # China makeup workdays -> Orange
US_HOLIDAY_CAT = 'Blue category'   # US holidays -> Blue

# Emoji icons
HOLIDAY_ICON = "🏝️"  # Island, represents vacation
WORK_ICON = "🧳"     # Luggage, represents commuting/work

# ====== Bilingual Name Mapping (English first, Chinese second) ======
# China holidays (Chinese -> English)
CN_NAME_MAP = {
    "元旦": "New Year's Day",
    "春节": "Spring Festival",
    "清明节": "Qingming Festival",
    "劳动节": "Labour Day",
    "端午节": "Dragon Boat Festival",
    "中秋节": "Mid-Autumn Festival",
    "国庆节": "National Day",
}

# US holidays (English -> Chinese)
US_NAME_MAP = {
    "New Year's Day": "元旦",
    "Martin Luther King Jr. Day": "马丁·路德·金纪念日",
    "Washington's Birthday": "华盛顿诞辰",
    "Memorial Day": "阵亡将士纪念日",
    "Juneteenth National Independence Day": "六月节",
    "Independence Day": "独立日",
    "Labor Day": "劳动节",
    "Columbus Day": "哥伦布日",
    "Veterans Day": "退伍军人节",
    "Thanksgiving Day": "感恩节",
    "Christmas Day": "圣诞节",
}

def generate_ics(events, filename):
    if not events:
        print(f"⚠️ Skipped empty calendar: {filename}")
        return

    cal = Calendar()
    cal.add('prodid', '-//Multi-Country Holiday Calendar//example.com//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('x-wr-calname', filename.split('.')[0])

    for event_data in events:
        event = Event()
        event.add('summary', event_data['name'])
        event.add('dtstart', event_data['date'])
        event.add('dtend', event_data['end_date'])
        event.add('dtstamp', datetime.utcnow())
        event.add('transp', 'TRANSPARENT')
        event.add('categories', event_data['category'])
        event.add('description', event_data.get('description', ''))
        cal.add_component(event)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(cal.to_ical())
    print(f"✅ Generated: {filepath} (Total: {len(events)} event ranges)")


def merge_dates(dates):
    if not dates:
        return []
    dates = sorted(set(dates))
    merged = []
    start = dates[0]
    end = dates[0]
    for d in dates[1:]:
        if d == end + timedelta(days=1):
            end = d
        else:
            merged.append((start, end))
            start = d
            end = d
    merged.append((start, end))
    return merged


# ========== Main Program ==========
print(f"Analyzing holidays and makeup workdays for {YEAR}...")

cn_holiday_dates = []
cn_work_dates = []

# ====== 1. Process China ======
try:
    current_date = date(YEAR, 1, 1)
    end_date = date(YEAR, 12, 31)
    
    while current_date <= end_date:
        is_workday = chinese_calendar.is_workday(current_date)
        is_weekend = current_date.weekday() >= 5
        
        if is_weekend and is_workday:
            cn_work_dates.append(current_date)
        else:
            on_holiday, holiday_name = chinese_calendar.get_holiday_detail(current_date)
            if on_holiday and holiday_name is not None:
                cn_holiday_dates.append(current_date)
        
        current_date += timedelta(days=1)
except NotImplementedError:
    print(f"⚠️ Error: chinesecalendar does not support {YEAR} yet. Please upgrade: pip install -U chinesecalendar")

# ====== 2. Process US ======
us_events = []
us_holidays = holidays.country_holidays('US', years=YEAR)
for h_date, h_name in us_holidays.items():
    # Get Chinese name based on English name
    cn_name = US_NAME_MAP.get(h_name, h_name)
    us_events.append({
        'date': h_date,
        'end_date': h_date + timedelta(days=1),
        'name': f"{HOLIDAY_ICON} [US] {h_name} {cn_name}",
        'category': US_HOLIDAY_CAT,
        'description': f"Country: US\nType: Public Holiday\nDate: {h_date}"
    })

# ====== 3. Merge China ranges ======
holiday_ranges = merge_dates(cn_holiday_dates)
work_ranges = merge_dates(cn_work_dates)

cn_events = []

# Generate China holidays (🏝️ [CN] English first, Chinese second)
for start, end in holiday_ranges:
    cn_name = chinese_calendar.get_holiday_detail(start)[1] or "Holiday"
    en_name = CN_NAME_MAP.get(cn_name, cn_name) # Get English name based on Chinese name
    
    if start == end:
        title = f"{HOLIDAY_ICON} [CN] {en_name} {cn_name}"
    else:
        title = f"{HOLIDAY_ICON} [CN] {en_name} {cn_name} ({start.month}/{start.day} - {end.month}/{end.day})"
        
    cn_events.append({
        'date': start,
        'end_date': end + timedelta(days=1),
        'name': title,
        'category': CN_HOLIDAY_CAT,
        'description': f"Country: China\nType: Statutory Holiday\nRange: {start} to {end}"
    })

# Generate China makeup workdays (🧳 [CN])
for start, end in work_ranges:
    if start == end:
        title = f"{WORK_ICON} [CN] Make up workday"
    else:
        title = f"{WORK_ICON} [CN] Make up workday ({start.month}/{start.day} - {end.month}/{end.day})"
        
    cn_events.append({
        'date': start,
        'end_date': end + timedelta(days=1),
        'name': title,
        'category': CN_WORK_CAT,
        'description': f"Country: China\nType: Weekend Makeup Workday\nRange: {start} to {end}"
    })

# ====== 4. Generate Files ======
print("\n===== Start generating calendar files =====")
generate_ics(cn_events, f"China_Holidays_{YEAR}.ics")
generate_ics(us_events, f"US_Holidays_{YEAR}.ics")

total_events = cn_events + us_events
generate_ics(total_events, f"All_Holidays_{YEAR}.ics")

print(f"\n📊 Statistics:")
print(f"   - China holiday ranges: {len(holiday_ranges)}")
print(f"   - China makeup workday ranges: {len(work_ranges)}")
print(f"   - US holidays: {len(us_events)}")
print(f"\n🎉 Generation complete! Everything is in English first, Chinese second, without the word 'Holiday'!")
