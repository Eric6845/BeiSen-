# -*- coding: utf-8 -*-
import os
import json
import re
import time
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# ====================== 1. 数据源配置 ======================
# 这里配置你要抓取的 RSS 源，可随时增删
DATA_SOURCES = [
    {
        "name": "36氪_投融资",
        "url": "https://36kr.com/feed",
        "type": "rss"
    },
    {
        "name": "投资界",
        "url": "https://pe.pedaily.cn/rss/",
        "type": "rss"
    },
    # 可继续添加其他 RSS，例如 TechCrunch、量子位等
]

# ====================== 2. 筛选规则（完全基于你之前的五大标准） ======================
# 深圳关键词
KEYWORDS_CITY = ["深圳", "鹏城", "深", "SZ"]
# 新兴赛道关键词（只要提及任一即算）
KEYWORDS_INDUSTRY = [
    "具身智能", "机器人", "半导体", "芯片", "AI", "人工智能", 
    "低空经济", "新能源", "储能", "生物医药", "合成生物", "智能硬件"
]
# 高成长关键词（融资、扩张等）
KEYWORDS_GROWTH = ["融资", "估值", "独角兽", "瞪羚", "专精特新", "IPO", "上市", "扩张", "亿元"]

# 排除关键词（避免头部巨头，这些关键词出现则过滤掉）
KEYWORDS_EXCLUDE = ["腾讯", "阿里巴巴", "百度", "字节", "京东", "美团", "网易", "拼多多", "滴滴", "小米", "华为", "中兴", "比亚迪"]

def is_relevant(title, summary):
    """
    判断一条新闻是否符合条件：
    1. 提到深圳或深圳企业
    2. 属于新兴赛道
    3. 有高成长特征（融资、扩张等）
    4. 不包含排除关键词
    """
    text = (title + " " + summary).lower()
    # 1. 检查城市
    city_ok = any(kw in text for kw in [k.lower() for k in KEYWORDS_CITY])
    if not city_ok:
        return False
    # 2. 检查行业
    industry_ok = any(kw in text for kw in [k.lower() for k in KEYWORDS_INDUSTRY])
    if not industry_ok:
        return False
    # 3. 检查成长特征
    growth_ok = any(kw in text for kw in [k.lower() for k in KEYWORDS_GROWTH])
    if not growth_ok:
        return False
    # 4. 检查排除词
    exclude_ok = not any(kw in text for kw in [k.lower() for k in KEYWORDS_EXCLUDE])
    if not exclude_ok:
        return False
    return True

# ====================== 3. 抓取函数 ======================
def fetch_rss(url):
    """抓取 RSS 并返回条目列表，每条为字典 {title, link, pub_date, summary}"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
        root = ET.fromstring(data)
        # 查找所有 item 元素（RSS 标准）
        items = []
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
            description = item.find('description').text if item.find('description') is not None else ''
            # 清洗 description 中的 HTML 标签
            description = re.sub('<[^<]+?>', '', description)
            items.append({
                'title': title.strip(),
                'link': link.strip(),
                'pub_date': pub_date.strip(),
                'summary': description.strip()[:500]  # 截取前500字符
            })
        return items
    except Exception as e:
        print(f"抓取 {url} 失败: {e}")
        return []

# ====================== 4. 去重机制（用文件记录已处理链接） ======================
HISTORY_FILE = "processed_links.txt"

def load_processed_links():
    """加载历史处理过的链接列表"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_processed_links(links):
    """保存处理过的链接"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        for link in links:
            f.write(link + '\n')

# ====================== 5. 从新闻中提取公司名和赛道（简单启发式） ======================
def extract_company_and_track(title, summary):
    """
    尝试从标题和摘要中提取一个公司名称和所属赛道。
    这里采用简单策略：寻找常见公司名称关键词，或根据行业关键词分配赛道。
    """
    text = title + " " + summary
    # 先尝试匹配常见的公司名模式（“XX公司”、“XX完成融资”等）
    # 简单起见，我们优先从标题中提取
    # 优先查找“XX完成”、“XX获得”等前面的词
    patterns = [
        r'([\u4e00-\u9fa5]{2,6})公司',
        r'([\u4e00-\u9fa5]{2,6})完成',
        r'([\u4e00-\u9fa5]{2,6})获得',
        r'([\u4e00-\u9fa5]{2,6})宣布',
    ]
    company = "未知企业"
    for pat in patterns:
        match = re.search(pat, title)
        if match:
            company = match.group(1)
            break
    # 如果还是未知，尝试从摘要中找
    if company == "未知企业":
        for pat in patterns:
            match = re.search(pat, summary)
            if match:
                company = match.group(1)
                break
    
    # 确定赛道：看文本中出现了哪个行业关键词
    track = "其他"
    for kw in KEYWORDS_INDUSTRY:
        if kw in text:
            track = kw
            break
    
    return company, track

# ====================== 6. 生成日报 ======================
def generate_html_report(news_items):
    """
    根据抓取到的新闻列表生成 HTML 日报。
    每条新闻视为一个“企业动态”，并尝试生成痛点话术（根据内容匹配）。
    """
    today_str = datetime.now().strftime("%Y年%m月%d日")
    
    # 如果没有新闻，显示无更新
    if not news_items:
        return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>北森拓客日报 {today_str}</title></head>
<body>
<h1>📋 北森拓客日报</h1>
<p>今日暂无符合条件的动态更新，请明天再查看。</p>
<p>日期：{today_str}</p>
</body>
</html>
"""
    
    # 按时间排序（假设 pub_date 存在，若无则用当前时间）
    for item in news_items:
        if not item.get('pub_date'):
            item['pub_date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    # 分类：S级（融资/IPO重大）、A级（合作/扩张）、B级（普通）
    s_list, a_list, b_list = [], [], []
    for item in news_items:
        text = item['title'] + " " + item['summary']
        if any(kw in text for kw in ["融资", "IPO", "上市", "递表", "受理", "辅导", "Pre-IPO"]):
            s_list.append(item)
        elif any(kw in text for kw in ["合作", "扩张", "量产", "发布", "基地", "获奖"]):
            a_list.append(item)
        else:
            b_list.append(item)
    
    # 构建HTML
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>北森拓客日报 {today_str}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background: #f0f4f8; padding: 20px; color: #1e293b; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
.header {{ background: linear-gradient(135deg, #1e293b, #0f172a); color: white; padding: 24px 30px; border-radius: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }}
.header h1 {{ font-size: 28px; font-weight: 700; }}
.header .date {{ font-size: 18px; opacity: 0.8; background: rgba(255,255,255,0.15); padding: 6px 16px; border-radius: 20px; }}
.stats {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
.stat-item {{ background: white; padding: 12px 24px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); flex: 1; min-width: 100px; text-align: center; }}
.stat-item .num {{ font-size: 28px; font-weight: 700; }}
.stat-item .label {{ font-size: 14px; color: #64748b; margin-top: 4px; }}
.stat-s .num {{ color: #dc2626; }}
.stat-a .num {{ color: #f59e0b; }}
.stat-b .num {{ color: #3b82f6; }}
.section {{ margin-bottom: 30px; }}
.section-title {{ font-size: 22px; font-weight: 700; padding: 12px 20px; border-radius: 12px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px; }}
.section-s .section-title {{ background: #fef2f2; color: #dc2626; border-left: 6px solid #dc2626; }}
.section-a .section-title {{ background: #fffbeb; color: #d97706; border-left: 6px solid #f59e0b; }}
.section-b .section-title {{ background: #eff6ff; color: #2563eb; border-left: 6px solid #3b82f6; }}
.card {{ background: white; border-radius: 12px; padding: 20px 24px; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); border-left: 5px solid #e2e8f0; }}
.card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
.card-s {{ border-left-color: #dc2626; }}
.card-a {{ border-left-color: #f59e0b; }}
.card-b {{ border-left-color: #3b82f6; }}
.card-header {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }}
.card-name {{ font-size: 20px; font-weight: 700; }}
.card-tag {{ background: #e2e8f0; padding: 2px 12px; border-radius: 20px; font-size: 13px; color: #475569; }}
.card-info {{ display: flex; flex-wrap: wrap; gap: 16px 24px; font-size: 14px; color: #475569; margin: 8px 0 10px 0; }}
.card-info span {{ background: #f8fafc; padding: 2px 10px; border-radius: 6px; }}
.card-dynamic {{ background: #f1f5f9; padding: 12px 16px; border-radius: 8px; margin: 10px 0; font-size: 15px; color: #0f172a; }}
.card-pain {{ background: #fefce8; padding: 12px 16px; border-radius: 8px; margin: 10px 0; border-left: 3px solid #eab308; }}
.card-pain .ptype {{ font-weight: 700; color: #92400e; }}
.card-pain .pdesc {{ margin-top: 4px; font-size: 14px; line-height: 1.6; color: #1e293b; }}
.card-stage {{ font-size: 13px; color: #3b82f6; font-weight: 600; }}
.footer {{ text-align: center; color: #94a3b8; font-size: 14px; margin-top: 30px; padding: 20px 0; border-top: 1px solid #e2e8f0; }}
@media (max-width: 640px) {{ .header {{ flex-direction: column; align-items: start; gap: 12px; }} .card {{ padding: 16px; }} }}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>📋 北森拓客日报</h1><span class="date">{today_str}</span></div>
<div class="stats">
<div class="stat-item stat-s"><div class="num">{len(s_list)}</div><div class="label">🔴 S级（重大动态）</div></div>
<div class="stat-item stat-a"><div class="num">{len(a_list)}</div><div class="label">🟡 A级（近期动态）</div></div>
<div class="stat-item stat-b"><div class="num">{len(b_list)}</div><div class="label">🔵 B级（关注中）</div></div>
<div class="stat-item"><div class="num">{len(news_items)}</div><div class="label">📊 总动态数</div></div>
</div>
"""

    # 渲染各层级
    for level, items, label in [
        ('s', s_list, 'S级 · 重大动态（融资/IPO进展）'),
        ('a', a_list, 'A级 · 近期动态（合作/扩张/发布）'),
        ('b', b_list, 'B级 · 关注中')
    ]:
        if items:
            html += f'<div class="section section-{level}"><div class="section-title">{"🔴" if level=="s" else "🟡" if level=="a" else "🔵"} {label}</div>'
            for item in items:
                # 提取公司名和赛道
                company, track = extract_company_and_track(item['title'], item['summary'])
                # 生成痛点话术（根据内容简单匹配）
                text = item['title'] + " " + item['summary']
                if any(kw in text for kw in ["IPO", "上市", "递表", "受理", "辅导"]):
                    pain_type = "IPO合规管理刚需"
                    pain_desc = "该公司正处于IPO关键阶段，上市合规对人力资源管理有严格要求，北森可提供合规级HR管理方案。"
                elif any(kw in text for kw in ["融资", "估值"]):
                    pain_type = "融资后快速扩张，组织管理跟不上"
                    pain_desc = "该公司近期获得融资，员工规模快速扩张，组织层级复杂化，北森一体化HCM平台可帮助分钟级完成组织调整。"
                elif any(kw in text for kw in ["研发", "算法", "芯片", "半导体"]):
                    pain_type = "研发驱动型，人才争夺激烈"
                    pain_desc = "该公司研发人员占比高，在激烈的人才争夺中，北森的全链路人才管理可助其系统性打赢人才战。"
                else:
                    pain_type = "组织管理数字化升级"
                    pain_desc = "该公司处于快速成长期，员工规模持续增长，北森一体化HCM平台可助力其实现人力资源全链路数字化管理。"
                
                html += f"""
<div class="card card-{level}">
<div class="card-header"><span class="card-name">{company}</span><span class="card-tag">{track}</span></div>
<div class="card-info"><span>📍 深圳</span><span>📰 {item.get('pub_date', '').split(' ')[0]}</span></div>
<div class="card-dynamic">📰 <a href="{item['link']}" target="_blank">{item['title']}</a><br><span style="font-size:14px;color:#475569;">{item['summary'][:200]}...</span></div>
<div class="card-pain"><div class="ptype">💡 核心痛点：{pain_type}</div><div class="pdesc">🎯 切入点：{pain_desc}</div></div>
</div>
"""
            html += '</div>'

    html += f"""
<div class="footer">数据来源：实时抓取自公开RSS（36氪、投资界等）<br>本日报由自动化系统生成，仅供内部业务拓展参考</div>
</div>
</body>
</html>
"""
    return html

# ====================== 7. 主程序 ======================
def main():
    # 加载历史链接
    processed = load_processed_links()
    new_items = []
    
    # 遍历所有数据源抓取
    for source in DATA_SOURCES:
        print(f"正在抓取: {source['name']}")
        items = fetch_rss(source['url'])
        for item in items:
            link = item['link']
            # 如果链接已处理过，跳过
            if link in processed:
                continue
            # 筛选
            if is_relevant(item['title'], item['summary']):
                # 检查日期是否在最近3天内（避免显示过旧新闻）
                try:
                    # 解析 pub_date 格式，如 "Mon, 10 Aug 2026 12:00:00 GMT"
                    pub = datetime.strptime(item['pub_date'], "%a, %d %b %Y %H:%M:%S %Z")
                except:
                    pub = datetime.now()  # 若解析失败则认为是今天
                if (datetime.now() - pub).days <= 3:
                    new_items.append(item)
                    processed.add(link)  # 加入已处理，避免重复
                else:
                    print(f"跳过过期新闻: {item['title'][:30]}...")
    
    # 保存更新后的历史链接
    save_processed_links(processed)
    
    # 按发布时间排序（最新的在前）
    new_items.sort(key=lambda x: x.get('pub_date', ''), reverse=True)
    
    # 生成日报
    html_content = generate_html_report(new_items)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ 日报已生成：index.html")
    print(f"📊 共抓取到 {len(new_items)} 条新动态")
    print("详细内容请查看 index.html")

if __name__ == "__main__":
    main()
