# -*- coding: utf-8 -*-
import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ====================== 1. RSS 数据源（已扩充至 8 个） ======================
RSS_SOURCES = [
    {"name": "36氪", "url": "https://36kr.com/feed"},
    {"name": "投资界", "url": "https://pe.pedaily.cn/rss/"},
    {"name": "创业邦", "url": "https://www.cyzone.cn/feed"},
    {"name": "亿欧网", "url": "https://www.iyiou.com/feed"},
    {"name": "动点科技", "url": "https://www.technode.com/feed"},
    {"name": "钛媒体", "url": "https://www.tmtpost.com/feed"},
    {"name": "虎嗅", "url": "https://www.huxiu.com/rss.xml"},
    {"name": "品玩", "url": "https://www.pingwest.com/feed"},
]

# ====================== 2. 公司名提取（增强版） ======================
CN_PATTERN = re.compile(
    r'([\u4e00-\u9fa5a-zA-Z0-9·]{2,12}?(?:科技|技术|智能|机器人|半导体|芯片|能源|生物|医药|医疗|信息|网络|数据|云|软件|硬件|系统|集成|装备|制造|材料|光电|微电子|电子|通信|自动化|无人机|航天|航空|公司|集团|有限|股份))'
)
QUOTE_PATTERN = re.compile(r'[「「『""\']([\u4e00-\u9fa5a-zA-Z0-9·]{2,10}?)[」」』""\']')
FINANCE_PATTERN = re.compile(
    r'([\u4e00-\u9fa5a-zA-Z0-9·]{2,12}?)\s*(?:完成|获|宣布|获得|新一轮|亿元|千万|融资|投资|A轮|B轮|C轮)'
)
EN_PATTERN = re.compile(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\s+(?:Raises|Secures|Closes|Announces|Launches|Acquires|Partners|Unveils|Introduces)')

def extract_company_name(text):
    if not text:
        return None
    m = QUOTE_PATTERN.search(text)
    if m:
        name = m.group(1).strip()
        if len(name) >= 2:
            return name
    m = CN_PATTERN.search(text)
    if m:
        name = m.group(1)
        for prefix in ['深圳', '北京', '上海', '广州', '杭州', '成都', '武汉', '南京', '苏州', '天津', '重庆']:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        return name.strip()
    m = FINANCE_PATTERN.search(text)
    if m:
        candidate = m.group(1).strip()
        exclude = ['项目', '产品', '平台', '系统', '技术', '方案', '服务', '企业', '行业', '市场', '领域', '中国', '团队', '资本', '投资']
        if len(candidate) >= 2 and candidate not in exclude:
            return candidate
    m = EN_PATTERN.search(text)
    if m:
        return m.group(1)
    return None

# ====================== 3. RSS 抓取函数（兼容多种格式） ======================
def fetch_rss_feed(url, max_entries=30, retry=2):
    for attempt in range(retry):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            break
        except Exception as e:
            if attempt == retry - 1:
                print(f"   ⚠️ 抓取失败 {url}: {e}")
                return []
            time.sleep(1)
    # 解析 RSS 2.0
    channel = root.find('channel')
    if channel is not None:
        items = channel.findall('item')
        articles = []
        for item in items[:max_entries]:
            title = item.find('title')
            link = item.find('link')
            pub_date = item.find('pubDate')
            description = item.find('description')
            articles.append({
                'title': title.text if title is not None else '',
                'link': link.text if link is not None else '',
                'pub_date': pub_date.text if pub_date is not None else '',
                'description': description.text if description is not None else ''
            })
        return articles
    # 解析 Atom
    entries = root.findall('entry')
    if entries:
        articles = []
        for entry in entries[:max_entries]:
            title = entry.find('title')
            link = entry.find('link')
            updated = entry.find('updated')
            summary = entry.find('summary')
            articles.append({
                'title': title.text if title is not None else '',
                'link': link.get('href') if link is not None and link.get('href') else '',
                'pub_date': updated.text if updated is not None else '',
                'description': summary.text if summary is not None else ''
            })
        return articles
    return []

# ====================== 4. 构建公司信息（优化后的宽松模式） ======================
def build_company_from_article(article, source_name):
    title = article.get('title', '') or ''
    desc = article.get('description', '') or ''
    link = article.get('link', '') or ''
    full_text = (title + " " + desc).strip()
    if len(full_text) < 10:
        return None

    company_name = extract_company_name(title) or extract_company_name(desc)
    if not company_name:
        return None
    if len(company_name) < 2 or company_name in ['数据', '技术', '平台', '系统', '产品', '项目', '资本']:
        return None

    # ----- 优化1：城市判断改为“若有则记录，若无则标记为未知，但仍通过” -----
    city_list = ['深圳', '北京', '上海', '广州', '杭州', '成都', '武汉', '南京', '苏州', '天津', '重庆', '西安', '长沙', '郑州', '青岛', '大连', '厦门', '合肥']
    city_found = None
    for city in city_list:
        if city in full_text:
            city_found = city
            break
    # 不再因城市未命中而返回 None，允许通过

    # ----- 优化2：赛道和成长关键词合并，要求至少命中一个 -----
    keywords = ['机器', '智能', '半导', '芯片', 'AI', '人工智', '低空', '无人', '新能源', '储能', '生物', '医药', '合成', '航天',
                '科技', '技术', '软件', '硬件', '电子', '通信', '光电', '装备', '制造', '材料', '医疗', '健康', '环保', '能源',
                '融资', '投资', '获', '完成', '亿元', '千万', '战略', '合作', '发布', '推出', '量产', '基地', '签约', '落地', '增长', '扩张']
    if not any(kw in full_text for kw in keywords):
        return None

    # 排除头部企业
    blacklist = ['腾讯', '阿里', '阿里巴巴', '百度', '华为', '字节', '字节跳动', '美团', '京东', '网易', '小米', '拼多多', '滴滴', '大疆', '谷歌', '微软', '亚马逊']
    if any(b in company_name or b in full_text for b in blacklist):
        return None

    # 构造动态内容
    dynamics = [f"{title}（来源：{source_name}）"]
    if link:
        dynamics.append(f"详情：{link}")

    # 赛道分类
    track = '其他'
    if any(kw in full_text for kw in ['机器', '智能']):
        track = '具身智能/机器人'
    elif any(kw in full_text for kw in ['半导', '芯片']):
        track = '半导体'
    elif any(kw in full_text for kw in ['AI', '人工智']):
        track = '人工智能'
    elif any(kw in full_text for kw in ['低空', '无人']):
        track = '低空经济'
    elif any(kw in full_text for kw in ['新能源', '储能']):
        track = '新能源'
    elif any(kw in full_text for kw in ['生物', '医药', '合成']):
        track = '生物医药'
    elif any(kw in full_text for kw in ['科技', '软件', '硬件']):
        track = '科技'
    elif any(kw in full_text for kw in ['制造', '装备']):
        track = '制造'

    # 发展阶段
    if any(kw in full_text for kw in ['融资', '投资', 'A轮', 'B轮', 'C轮']):
        stage = '快速扩张期'
    elif any(kw in full_text for kw in ['IPO', '上市', 'Pre-IPO']):
        stage = 'IPO冲刺期'
    elif any(kw in full_text for kw in ['合作', '战略合作']):
        stage = '战略合作期'
    elif any(kw in full_text for kw in ['发布', '推出']):
        stage = '产品发布期'
    else:
        stage = '成长期'

    return {
        "name": company_name,
        "track": track,
        "employees": '未知',
        "finance": '',
        "branches": city_found or '未知',
        "rd_ratio": '',
        "honor": '',
        "stage": stage,
        "dynamics": dynamics
    }

# ====================== 5. 抓取主函数 ======================
def fetch_companies_from_rss():
    all_companies = []
    seen_names = set()
    print("🔍 开始抓取所有 RSS 源（宽松模式）...")
    for source in RSS_SOURCES:
        articles = fetch_rss_feed(source['url'])
        print(f"📡 {source['name']} 抓取到 {len(articles)} 篇文章")
        for article in articles:
            company = build_company_from_article(article, source['name'])
            if company and company['name'] not in seen_names:
                seen_names.add(company['name'])
                all_companies.append(company)
                print(f"   ✅ 通过: {company['name']} ({company['track']}) @ {company['branches']}")
        time.sleep(0.5)
    print(f"✅ 总共抓取到 {len(all_companies)} 家合格公司")
    return all_companies

# ====================== 6. 保底名单（精简至5家，仅供不足时补充） ======================
MANUAL_COMPANIES = [
    {"name": "逐际动力", "track": "具身智能", "employees": "快速扩张中", "finance": "Pre-IPO轮近2亿美元", "branches": "深圳", "stage": "Pre-IPO冲刺期", "dynamics": ["2026年7月14日完成近2亿美元Pre-IPO轮融资（来源：新华社）"]},
    {"name": "埃芯半导体", "track": "半导体", "employees": "近300人", "finance": "B+轮近10亿元", "branches": "深圳", "stage": "快速扩张期", "dynamics": ["2026年7月29日完成近10亿元B+轮融资（来源：投资界）"]},
    {"name": "智平方", "track": "具身智能", "employees": "快速扩张中", "finance": "估值超200亿元", "branches": "深圳", "stage": "高速融资扩张期", "dynamics": ["2026年6月完成近50亿元融资（来源：投资者网）"]},
    {"name": "地瓜机器人", "track": "具身智能", "employees": "300+人", "finance": "B轮累计2.7亿美元", "branches": "深圳", "stage": "规模化扩张期", "dynamics": ["2026年4月完成B2轮1.5亿美元融资（来源：36氪）"]},
    {"name": "众擎机器人", "track": "具身智能", "employees": "130+人", "finance": "B轮2亿美元", "branches": "深圳", "stage": "量产交付突破期", "dynamics": ["2026年4月完成2亿美元B轮融资（来源：投资界）"]},
]

# ====================== 7. 主入口：优化4（阈值调整为4家） ======================
def get_all_companies():
    rss_companies = fetch_companies_from_rss()
    # 如果抓取到 4 家及以上，直接返回前8家（不再补充保底）
    if len(rss_companies) >= 4:
        return rss_companies[:8]
    # 否则补充保底名单至至少6家
    combined = rss_companies.copy()
    existing = set(c['name'] for c in combined)
    for manual in MANUAL_COMPANIES:
        if manual['name'] not in existing:
            combined.append(manual)
            existing.add(manual['name'])
        if len(combined) >= 6:
            break
    return combined[:8]

# ====================== 8. 痛点匹配 ======================
def match_pain_point(company):
    stage = company.get("stage", "")
    if "IPO" in stage or "Pre-IPO" in stage:
        return {"type": "IPO合规管理刚需", "desc": "贵公司正处于IPO关键期，北森可提供合规级HR管理方案。"}
    if "扩张" in stage or "融资" in stage:
        return {"type": "融资后快速扩张", "desc": "北森一体化HCM平台帮助组织调整分钟级完成。"}
    if "半导体" in company.get("track", "") or "研发" in company.get("employees", ""):
        return {"type": "研发驱动型，人才争夺激烈", "desc": "北森全链路人才管理帮您系统性打赢人才战。"}
    return {"type": "组织管理数字化升级", "desc": "北森一体化HCM平台实现人力资源全链路数字化。"}

def get_today_dynamic(company):
    today = datetime.now()
    seed = today.year * 10000 + today.month * 100 + today.day
    name_hash = sum([ord(c) for c in company["name"]])
    dyn_list = company.get("dynamics", [])
    if not dyn_list:
        return "暂无动态"
    idx = (seed + name_hash) % len(dyn_list)
    return dyn_list[idx]

# ====================== 9. 生成 HTML（与之前一致） ======================
def generate_html_report():
    today_str = datetime.now().strftime("%Y年%m月%d日")
    all_companies = get_all_companies()
    if not all_companies:
        return f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>北森拓客日报</title></head>
<body style="font-family:Arial;text-align:center;padding:50px;">
<h1>📋 北森拓客日报</h1><p>{today_str}</p>
<p>今日暂无符合条件的动态更新</p>
</body></html>
"""
    s_list, a_list, b_list = [], [], []
    for comp in all_companies:
        dynamic = get_today_dynamic(comp)
        pain = match_pain_point(comp)
        comp["today_dynamic"] = dynamic
        comp["pain_point"] = pain
        if any(kw in dynamic for kw in ["融资", "IPO", "上市"]):
            s_list.append(comp)
        elif any(kw in dynamic for kw in ["合作", "发布", "量产"]):
            a_list.append(comp)
        else:
            b_list.append(comp)

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
<div class="stat-item"><div class="num">{len(all_companies)}</div><div class="label">📊 总企业数</div></div>
</div>
"""
    for level, items, label in [
        ("s", s_list, "S级 · 重大动态（融资/IPO）"),
        ("a", a_list, "A级 · 近期动态（合作/发布）"),
        ("b", b_list, "B级 · 关注中")
    ]:
        if items:
            emoji = "🔴" if level == "s" else "🟡" if level == "a" else "🔵"
            html += f'<div class="section section-{level}"><div class="section-title">{emoji} {label}</div>'
            for comp in items:
                pain = comp["pain_point"]
                html += f"""
<div class="card card-{level}">
<div class="card-header"><span class="card-name">{comp['name']}</span><span class="card-tag">{comp['track']}</span></div>
<div class="card-info"><span>👥 {comp['employees']}</span><span>📍 {comp['branches']}</span><span class="card-stage">📌 {comp['stage']}</span></div>
<div class="card-dynamic">📰 {comp['today_dynamic']}</div>
<div class="card-pain"><div class="ptype">💡 {pain['type']}</div><div class="pdesc">🎯 {pain['desc']}</div></div>
</div>
"""
            html += '</div>'
    html += f"""
<div class="footer">数据来源：公开RSS订阅源（36氪、投资界、创业邦、亿欧网、动点科技、钛媒体、虎嗅、品玩）<br>本日报由自动化系统生成，仅供内部业务拓展参考</div>
</div>
</body>
</html>
"""
    return html

# ====================== 10. 主程序（带异常捕获） ======================
if __name__ == "__main__":
    try:
        print("🚀 脚本开始运行...")
        html_content = generate_html_report()
        print(f"📄 HTML 内容长度: {len(html_content)} 字符")
        filename = "index.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✅ 日报已生成：{filename}")
        companies = get_all_companies()
        print(f"📊 共 {len(companies)} 家企业")
    except Exception as e:
        print(f"❌ 脚本运行出错: {e}")
        import traceback
        traceback.print_exc()
        try:
            with open("index.html", "w", encoding="utf-8") as f:
                f.write(f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>北森拓客日报</title></head>
<body style="font-family:Arial;text-align:center;padding:50px;">
<h1>📋 北森拓客日报</h1>
<p style="color:#64748b;">{datetime.now().strftime('%Y年%m月%d日')}</p>
<p style="color:#dc2626;">⚠️ 脚本运行出错，请查看 Actions 日志</p>
<p style="color:#94a3b8;font-size:14px;">错误信息: {e}</p>
</body>
</html>
""")
            print("🛠️ 已生成错误提示页面 index.html")
        except:
            pass
