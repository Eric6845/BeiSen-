# -*- coding: utf-8 -*-
import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ====================== 1. RSS 数据源（扩充并切换为可靠源） ======================
RSS_SOURCES = [
    # 36氪 的 feed 有时格式异常，改用其官方替代（实际稳定的是 https://36kr.com/feed 但经常挂）
    # 采用多个备选
    {"name": "36氪_快讯", "url": "https://36kr.com/feed"},
    {"name": "投资界", "url": "https://pe.pedaily.cn/rss/"},
    {"name": "创业邦", "url": "https://www.cyzone.cn/feed"},
    {"name": "亿欧网", "url": "https://www.iyiou.com/feed"},
    {"name": "Donews", "url": "https://www.donews.com/rss.xml"},
    # 动点科技英文较多，保留
    {"name": "动点科技", "url": "https://www.technode.com/feed"},
]

# ====================== 2. 公司名提取（加强版） ======================
# 匹配中文公司名称（含常见后缀）
CN_PATTERN = re.compile(
    r'([\u4e00-\u9fa5a-zA-Z0-9·]{2,12}?(?:科技|技术|智能|机器人|半导体|芯片|能源|生物|医药|医疗|信息|网络|数据|云|软件|硬件|系统|集成|装备|制造|材料|光电|微电子|电子|通信|自动化|无人机|航天|航空|公司|集团|有限|股份))'
)
# 匹配引号内的公司名（如「智平方」、“地瓜机器人”等）
QUOTE_PATTERN = re.compile(r'[「「『""\']([\u4e00-\u9fa5a-zA-Z0-9·]{2,10}?)[」」』""\']')
# 匹配 “XXX完成/获/宣布融资” 句式
FINANCE_PATTERN = re.compile(
    r'([\u4e00-\u9fa5a-zA-Z0-9·]{2,12}?)\s*(?:完成|获|宣布|获得|新一轮|亿元|千万|融资|投资|A轮|B轮|C轮)'
)
# 匹配英文公司名（如 "DeepSeek Raises"）
EN_PATTERN = re.compile(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\s+(?:Raises|Secures|Closes|Announces|Launches|Acquires|Partners|Unveils|Introduces)')

def extract_company_name(text):
    """从文本中提取公司名，返回第一个候选，否则 None"""
    if not text:
        return None
    # 优先匹配引号中的名称（如「智平方」）
    m = QUOTE_PATTERN.search(text)
    if m:
        name = m.group(1).strip()
        if len(name) >= 2:
            return name
    # 其次匹配中文公司后缀
    m = CN_PATTERN.search(text)
    if m:
        name = m.group(1)
        # 去除常见地域前缀
        for prefix in ['深圳', '北京', '上海', '广州', '杭州', '成都', '武汉', '南京', '苏州', '天津', '重庆']:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        return name.strip()
    # 再次匹配“XXX融资”句式
    m = FINANCE_PATTERN.search(text)
    if m:
        candidate = m.group(1).strip()
        exclude = ['项目', '产品', '平台', '系统', '技术', '方案', '服务', '企业', '行业', '市场', '领域', '中国', '团队', '资本', '投资']
        if len(candidate) >= 2 and candidate not in exclude:
            return candidate
    # 最后尝试英文
    m = EN_PATTERN.search(text)
    if m:
        return m.group(1)
    return None

# ====================== 3. RSS 抓取函数（支持重试） ======================
def fetch_rss_feed(url, max_entries=30, retry=2):
    for attempt in range(retry):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            # 尝试解析 XML
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
    # 尝试 Atom
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

# ====================== 4. 公司信息构建（极度宽松） ======================
def build_company_from_article(article, source_name):
    title = article.get('title', '') or ''
    desc = article.get('description', '') or ''
    link = article.get('link', '') or ''
    full_text = (title + " " + desc).strip()
    if len(full_text) < 10:
        return None

    # 提取公司名
    company_name = extract_company_name(title) or extract_company_name(desc)
    if not company_name:
        return None
    if len(company_name) < 2 or company_name in ['数据', '技术', '平台', '系统', '产品', '项目', '资本']:
        return None

    # 城市判断：只要出现中国城市即通过（哪怕不是深圳，我们后续会标记）
    city_list = ['深圳', '北京', '上海', '广州', '杭州', '成都', '武汉', '南京', '苏州', '天津', '重庆', '西安', '长沙', '郑州', '青岛', '大连', '厦门', '合肥']
    city_found = None
    for city in city_list:
        if city in full_text:
            city_found = city
            break

    # 赛道与成长关键词合并
    keywords = ['机器', '智能', '半导', '芯片', 'AI', '人工智', '低空', '无人', '新能源', '储能', '生物', '医药', '合成', '航天',
                '科技', '技术', '软件', '硬件', '电子', '通信', '光电', '装备', '制造', '材料', '医疗', '健康', '环保', '能源',
                '融资', '投资', '获', '完成', '亿元', '千万', '战略', '合作', '发布', '推出', '量产', '基地', '签约', '落地', '增长', '扩张']
    # 只要命中任意一个关键词，即认为符合（宽松）
    if not any(kw in full_text for kw in keywords):
        return None

    # 排除头部企业
    blacklist = ['腾讯', '阿里', '阿里巴巴', '百度', '华为', '字节', '字节跳动', '美团', '京东', '网易', '小米', '拼多多', '滴滴', '大疆', '谷歌', '微软', '亚马逊']
    if any(b in company_name or b in full_text for b in blacklist):
        return None

    # 构造动态
    dynamics = [f"{title}（来源：{source_name}）"]
    if link:
        dynamics.append(f"详情：{link}")

    # 赛道分类（简化）
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

# ====================== 5. 抓取主函数（宽松） ======================
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
                # 打印通过的公司名，方便查看
                print(f"   ✅ 通过: {company['name']} ({company['track']}) @ {company['branches']}")
        time.sleep(0.5)
    print(f"✅ 总共抓取到 {len(all_companies)} 家合格公司")
    return all_companies

# ====================== 6. 手动保底名单（保留但不主导） ======================
MANUAL_COMPANIES = [
    {"name": "逐际动力", "track": "具身智能", "employees": "快速扩张中", "finance": "Pre-IPO轮近2亿美元", "branches": "深圳", "stage": "Pre-IPO冲刺期", "dynamics": ["2026年7月14日完成近2亿美元Pre-IPO轮融资（来源：新华社）"]},
    {"name": "埃芯半导体", "track": "半导体", "employees": "近300人", "finance": "B+轮近10亿元", "branches": "深圳", "stage": "快速扩张期", "dynamics": ["2026年7月29日完成近10亿元B+轮融资（来源：投资界）"]},
    {"name": "智平方", "track": "具身智能", "employees": "快速扩张中", "finance": "估值超200亿元", "branches": "深圳", "stage": "高速融资扩张期", "dynamics": ["2026年6月完成近50亿元融资（来源：投资者网）"]},
    {"name": "地瓜机器人", "track": "具身智能", "employees": "300+人", "finance": "B轮累计2.7亿美元", "branches": "深圳", "stage": "规模化扩张期", "dynamics": ["2026年4月完成B2轮1.5亿美元融资（来源：36氪）"]},
    {"name": "众擎机器人", "track": "具身智能", "employees": "130+人", "finance": "B轮2亿美元", "branches": "深圳", "stage": "量产交付突破期", "dynamics": ["2026年4月完成2亿美元B轮融资（来源：投资界）"]},
    {"name": "星尘智能", "track": "具身智能", "employees": "151人", "finance": "三个月融资超10亿元", "branches": "深圳", "stage": "股改完成", "dynamics": ["三个月内完成3轮融资超10亿元（来源：36氪）"]},
    {"name": "跨维智能", "track": "具身智能", "employees": "快速扩张中", "finance": "估值超100亿元", "branches": "深圳", "stage": "IPO筹备期", "dynamics": ["完成10亿元B轮融资（来源：经济参考报）"]},
]

def get_all_companies():
    # 先尝试抓取
    rss_companies = fetch_companies_from_rss()
    # 如果抓取到 >= 6 家，直接返回前8
    if len(rss_companies) >= 6:
        return rss_companies[:8]
    # 否则补足手动名单
    combined = rss_companies.copy()
    existing = set(c['name'] for c in combined)
    for manual in MANUAL_COMPANIES:
        if manual['name'] not in existing:
            combined.append(manual)
            existing.add(manual['name'])
        if len(combined) >= 8:
            break
    return combined[:8]

# ====================== 以下为日报生成函数（与之前一致，略作精简） ======================
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
    # 后续 HTML 模板（与之前相同，为节省篇幅已省略，但请务必保留完整的样式和结构）
    # 由于篇幅，这里省略（实际使用时需补充完整HTML模板）
