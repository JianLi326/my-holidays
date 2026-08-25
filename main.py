from datetime import datetime, date
import holidays
from icalendar import Calendar, Event
import os

YEAR = 2026
OUTPUT_DIR = "output"

COUNTRIES = [
    {'code': 'CN', 'country_name': '中国', 'tag': '🇨🇳 中国', 'search_keys': ['中国', 'China', 'CN']},
    {'code': 'US', 'country_name': '美国', 'tag': '🇺🇸 美国', 'search_keys': ['美国', 'US', 'USA']},
]

company_holidays = [
    
]

def generate_ics(events, filename):
    if not events:
        return
    cal = Calendar()
    cal.add('prodid', '-//Multi-Country Holiday Calendar//example.com//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('x-wr-calname', filename.split('.')[0])

    for event_data in events:
        event = Event()
        search_keys_str = " / ".join(event_data.get('search_keys', []))
        event.add('summary', f"{event_data['name']} [{search_keys_str}]")
        event.add('dtstart', event_data['date'])
        event.add('dtend', event_data['date'])
        event.add('dtstamp', datetime.utcnow())
        event.add('transp', 'TRANSPARENT')
        event.add('categories', event_data['category'])
        
        search_text = f"{event_data['country_name']} {event_data.get('type', '')}"
        if 'search_keys' in event_data:
            search_text += " " + " ".join(event_data['search_keys'])
        event.add('description', f"国家/地区: {event_data['country_name']}\n搜索关键词: {search_text}\n原始名称: {event_data['name']}")

        cal.add_component(event)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(cal.to_ical())
    print(f"✅ 已生成: {filepath} (共 {len(events)} 个事件)")

all_events = {'CN': [], 'US': [], 'Company': []}

for country_config in COUNTRIES:
    code = country_config['code']
    tag = country_config['tag']
    country_name = country_config['country_name']
    country_holidays = holidays.country_holidays(code, years=YEAR)
    for holiday_date, holiday_name in country_holidays.items():
        all_events[code].append({
            'date': holiday_date, 'name': f"{tag} {holiday_name}",
            'type': f'{country_name}公共假期', 'category': tag,
            'country_code': code, 'country_name': country_name,
            'search_keys': country_config['search_keys']
        })

for item in company_holidays:
    all_events['Company'].append({
        'date': item['date'], 'name': f"{item['tag']} {item['name']}",
        'type': item['type'], 'category': item['tag'],
        'country_code': item.get('country_code', 'Other'),
        'country_name': item.get('country_name', '其他'),
        'search_keys': [item.get('country_name', '其他'), '公司']
    })

print("开始生成日历...")
generate_ics(all_events['CN'], f"China_Holidays_{YEAR}.ics")
generate_ics(all_events['US'], f"US_Holidays_{YEAR}.ics")
generate_ics(all_events['Company'], f"Company_Events_{YEAR}.ics")
total_events = all_events['CN'] + all_events['US'] + all_events['Company']
generate_ics(total_events, f"All_Holidays_{YEAR}.ics")
print("生成完毕！")
