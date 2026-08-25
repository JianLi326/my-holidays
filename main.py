from datetime import datetime, date
import holidays
from icalendar import Calendar, Event
import os

# ========== 配置区 ==========
YEAR = 2026
OUTPUT_DIR = "output"  # 所有文件会保存在这个文件夹里，避免弄乱目录

# 定义国家和对应的标签
COUNTRIES = [
    {
        'code': 'CN', 
        'country_name': '中国', 
        'tag': '🇨🇳 中国',
        'search_keys': ['中国', 'China', 'CN']
    },
    {
        'code': 'US', 
        'country_name': '美国', 
        'tag': '🇺🇸 美国',
        'search_keys': ['美国', 'US', 'USA']  # 去掉了重复的'美国'
    },
]

# ====== 新增：添加公司节日（补齐了 country_code 用于正确统计） ======
company_holidays = [
    # 中国的公司节日
    {'date': date(2026, 9, 1), 'name': '公司周年庆', 'type': '公司活动', 
     'tag': '🏢 中国公司', 'country_name': '中国', 'country_code': 'CN'},
    # 美国的公司节日
    {'date': date(2026, 12, 25), 'name': '公司圣诞派对', 'type': '公司活动', 
     'tag': '🎄 美国公司', 'country_name': '美国', 'country_code': 'US'},
    {'date': date(2026, 7, 4), 'name': '独立日庆祝活动', 'type': '公司活动', 
     'tag': '🎆 美国公司', 'country_name': '美国', 'country_code': 'US'},
]
# ===========================

def generate_ics(events, filename):
    """根据事件列表生成对应的 ICS 文件"""
    if not events:
        print(f"⚠️ 跳过空日历: {filename}")
        return

    cal = Calendar()
    cal.add('prodid', '-//Multi-Country Holiday Calendar//example.com//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    # 给日历一个可读的名字，方便在 Outlook 左侧直接显示
    cal.add('x-wr-calname', filename.split('.')[0]) 

    for event_data in events:
        event = Event()
        
        # ====== 关键优化：直接把搜索关键词拼接进标题 ======
        # 这样在 Outlook 搜索框搜 "USA"、"CN" 都能直接搜到
        search_keys_str = " / ".join(event_data.get('search_keys', []))
        event.add('summary', f"{event_data['name']} [{search_keys_str}]")
        
        event.add('dtstart', event_data['date'])
        event.add('dtend', event_data['date'])
        # 修正为 UTC 标准时间戳，避免时区错乱
        event.add('dtstamp', datetime.utcnow()) 
        event.add('transp', 'TRANSPARENT')
        
        # 添加分类（用于 Outlook 分类/着色）
        event.add('categories', event_data['category'])
        
        # 在描述中添加搜索关键词
        search_text = f"{event_data['country_name']} {event_data.get('type', '')}"
        if 'search_keys' in event_data:
            search_text += " " + " ".join(event_data['search_keys'])
        
        event.add('description', f"国家/地区: {event_data['country_name']}\n搜索关键词: {search_text}\n原始名称: {event_data['name']}")

        cal.add_component(event)

    # 确保输出文件夹存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(cal.to_ical())
    print(f"✅ 已生成: {filepath} (共 {len(events)} 个事件)")


# ========== 主程序 ==========
print(f"正在生成 {YEAR} 年多国节假日日历...")

# 用字典按类别收集事件
all_events = {
    'CN': [],
    'US': [],
    'Company': []
}

# 1. 获取所有国家的公共假期
for country_config in COUNTRIES:
    code = country_config['code']
    tag = country_config['tag']
    country_name = country_config['country_name']
    
    print(f"  正在获取 {country_name} ({code}) 的假期...")
    
    # 获取该国家的假期
    country_holidays = holidays.country_holidays(code, years=YEAR)
    
    for holiday_date, holiday_name in country_holidays.items():
        all_events[code].append({
            'date': holiday_date,
            'name': f"{tag} {holiday_name}",
            'type': f'{country_name}公共假期',
            'category': tag,
            'country_code': code,
            'country_name': country_name,
            'search_keys': country_config['search_keys']
        })

# 2. 添加公司节日
for item in company_holidays:
    all_events['Company'].append({
        'date': item['date'],
        'name': f"{item['tag']} {item['name']}",
        'type': item['type'],
        'category': item['tag'],
        'country_code': item.get('country_code', 'Other'),
        'country_name': item.get('country_name', '其他'),
        'search_keys': [item.get('country_name', '其他'), '公司']
    })

# ====== 生成多个独立的 ICS 文件（完美解决 Outlook 无法按需筛选的问题） ======
print("\n===== 开始生成独立日历文件 =====")
generate_ics(all_events['CN'], f"中国假期_{YEAR}.ics")
generate_ics(all_events['US'], f"美国假期_{YEAR}.ics")
generate_ics(all_events['Company'], f"公司活动_{YEAR}.ics")

# 同时也生成一个包含所有节日的汇总文件（如果你想看全貌，可以直接勾选这个）
total_events = all_events['CN'] + all_events['US'] + all_events['Company']
generate_ics(total_events, f"全部节假日_{YEAR}.ics")

# ====== 统计打印 ======
print(f"\n📊 统计信息:")
print(f"   - 中国假期: {len(all_events['CN'])} 个")
print(f"   - 美国假期: {len(all_events['US'])} 个")
print(f"   - 公司节日: {len(all_events['Company'])} 个")
print(f"\n🎉 全部生成完毕！")
print(f"👉 请打开 'output' 文件夹，将这 4 个 .ics 文件导入 Outlook。")
print(f"👉 导入后，在 Outlook 左侧边栏，你可以像勾选开关一样，独立显示/隐藏这几个日历。")