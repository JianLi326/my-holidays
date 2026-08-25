from datetime import datetime, date, timedelta
import chinese_calendar
import holidays
from icalendar import Calendar, Event
import os

# ========== Configuration ==========
current_date_now = datetime.now()
if current_date_now.month >= 11:
    YEAR = current_date_now.year + 1
else:
    YEAR = current_date_now.year

OUTPUT_DIR = "output"

CN_HOLIDAY_CAT = 'Red category'
CN_WORK_CAT = 'Orange category'
US_HOLIDAY_CAT = 'Blue category'
COMPANY_HOLIDAY_CAT = 'Green category'

HOLIDAY_ICON = "🏝️"
WORK_ICON = "🧳"
COMPANY_ICON = "🎉"

# ====== Custom Holidays / Events (Mix of Company & US Extra) ======
def get_day_after_thanksgiving(year):
    d = date(year, 11, 1)
    while d.weekday() != 3:  # 3 = Thursday
        d += timedelta(days=1)
    d += timedelta(weeks=3)
    return d + timedelta(days=1)

# Set 'is_us' to True for US holidays (uses blue color, joins US file), False for Company (uses green color)
COMPANY_HOLIDAYS = [
    {"date": get_day_after_thanksgiving(YEAR), "name": "Day After Thanksgiving", "is_us": True},
    # {"date": date(2026, 4, 30), "name": "公司成立纪念日", "is_us": False},
]

# ====== Bilingual Name Mapping ======
CN_NAME_MAP = {
    "New Year's Day": "元旦",
    "Spring Festival": "春节",
    "Chinese New Year": "春节",
    "Qingming Festival": "清明节",
    "Tomb-sweeping Day": "清明节",
    "Tomb-Sweeping Day": "清明节",
    "Labour Day": "劳动节",
    "Labor Day": "劳动节",
    "Dragon Boat Festival": "端午节",
    "Mid-Autumn Festival": "中秋节",
    "Mid-autumn Festival": "中秋节",
    "Mid-Autumn": "中秋节",
    "National Day": "国庆节",
}

def normalize_name(name):
    if not name:
        return name
    lowered = name.lower()
    for key in CN_NAME_MAP:
        if key.lower() == lowered:
            return key
    return name

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
    "Day After Thanksgiving": "感恩节次日",
}

def generate_ics(events, filename):
    if not events:
        print(f"Skipped empty calendar: {filename}")
        return

    cal = Calendar()
    cal.add('prodid', '-//Multi-Country Holiday Calendar//example.com//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', filename.split('.')[0])
    cal.add('x-wr-caldesc', 'Auto-generated holidays, makeup workdays, and company events.')
    cal.add('class', 'PUBLIC')

    from icalendar import Timezone, TimezoneStandard
    tz = Timezone()
    tz.add('tzid', 'Asia/Shanghai')
    std = TimezoneStandard()
    std.add('dtstart', datetime(1970, 1, 1))
    std.add('tzoffsetfrom', timedelta(hours=8))
    std.add('tzoffsetto', timedelta(hours=8))
    tz.add_component(std)
    cal.add_component(tz)

    for event_data in events:
        event = Event()
        event.add('summary', event_data['name'])
        event.add('dtstart', event_data['date'])
        event.add('dtend', event_data['end_date'])
        event.add('dtstamp', datetime.utcnow())
        event.add('transp', 'TRANSPARENT')
        event.add('categories', event_data['category'])
        event.add('description', event_data.get('description', '').replace('\n', ' '))
        uid_str = f"{event_data['date']}/{event_data['end_date']}/{filename.split('.')[0]}"
        event.add('uid', uid_str)
        cal.add_component(event)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(cal.to_ical())
    print(f"Generated: {filepath} (Total: {len(events)} events)")


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
    print(f"Error: chinesecalendar does not support {YEAR} yet. Please upgrade.")


# ====== 1. Process US ======
us_events = []
us_holidays = holidays.country_holidays('US', years=YEAR)
for h_date, h_name in us_holidays.items():
    cn_name = US_NAME_MAP.get(h_name, h_name)
    us_events.append({
        'date': h_date,
        'end_date': h_date + timedelta(days=1),
        'name': f"{HOLIDAY_ICON} [US] {h_name} ({cn_name})",
        'category': US_HOLIDAY_CAT,
        'description': f"US Holiday: {h_name} ({cn_name})"
    })


# ====== 2. Merge and Process China ======
holiday_ranges = merge_dates(cn_holiday_dates)
work_ranges = merge_dates(cn_work_dates)

cn_events = []

# Generate China Holidays
for start, end in holiday_ranges:
    raw_name = chinese_calendar.get_holiday_detail(start)[1] or "Holiday"
    en_name = normalize_name(raw_name)
    cn_name = CN_NAME_MAP.get(en_name, "")
    
    if cn_name:
        title = f"{HOLIDAY_ICON} [CN] {en_name} ({cn_name})"
    else:
        title = f"{HOLIDAY_ICON} [CN] {en_name}"
        
    cn_events.append({
        'date': start,
        'end_date': end + timedelta(days=1),
        'name': title,
        'category': CN_HOLIDAY_CAT,
        'description': f"CN Holiday: {en_name} ({cn_name})"
    })

# Generate China Makeup Workdays
for start, end in work_ranges:
    title = f"{WORK_ICON} [CN] Make-up workday (调休补班)"
    cn_events.append({
        'date': start,
        'end_date': end + timedelta(days=1),
        'name': title,
        'category': CN_WORK_CAT,
        'description': "CN Makeup workday (调休补班)"
    })


# ====== 3. Process Custom Holidays (Company + US Extra) ======
company_events = []
for item in COMPANY_HOLIDAYS:
    if item['date'].year == YEAR:
        # 判定：如果是 is_us=True，则用 US 的蓝色和 🏝️ 图标，并加入 US 日历
        if item.get('is_us', False):
            us_events.append({
                'date': item['date'],
                'end_date': item['date'] + timedelta(days=1),
                'name': f"{HOLIDAY_ICON} [US] {item['name']} ({US_NAME_MAP.get(item['name'], item['name'])})",
                'category': US_HOLIDAY_CAT,
                'description': f"US Holiday: {item['name']}"
            })
        # 如果不是 US，则是普通公司节日，用绿色和 🎉 图标
        else:
            company_events.append({
                'date': item['date'],
                'end_date': item['date'] + timedelta(days=1),
                'name': f"{COMPANY_ICON} [Company] {item['name']}",
                'category': COMPANY_HOLIDAY_CAT,
                'description': f"Company Event"
            })


# ====== 4. Generate Files ======
print("\n===== Start generating calendar files =====")
generate_ics(cn_events, f"China_Holidays_{YEAR}.ics")
generate_ics(us_events, f"US_Holidays_{YEAR}.ics")
generate_ics(company_events, f"Company_Holidays_{YEAR}.ics")

total_events = cn_events + us_events + company_events
generate_ics(total_events, f"All_Holidays_{YEAR}.ics")

print(f"\nStatistics:")
print(f"   - China holiday ranges: {len(holiday_ranges)}")
print(f"   - China makeup workday ranges: {len(work_ranges)}")
print(f"   - US holidays: {len(us_events)}")
print(f"   - Company events: {len(company_events)}")
print(f"\nGeneration complete!")
