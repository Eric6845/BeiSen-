# -*- coding: utf-8 -*-
import os
import json
import random
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ====================== RSS 数据源配置（扩充） ======================
RSS_SOURCES = [
    {"name": "36氪_投融资", "url": "https://36kr.com/feed"},
    {"name": "投资界", "url": "https://pe.pedaily.cn/rss/"},
    {"name": "量子位", "url": "https://www.qbitai.com/feed"},
    {"name": "动点科技", "url": "https://www.technode.com/feed"},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss"},
    {"name": "IT桔子", "url": "https://www.itjuzi.com/feed"},
    {"name": "猎云网", "url": "https://www.lieyunwang.com/feed"},
    {"name": "亿欧网", "url": "https://www.iyiou.com/feed"},
]

# ====================== 公司名提取工具（增强版） ======================
# 匹配“XX公司”、“XX科技”、“XX智能”等
COMPANY_PATTERN = re.compile(r'([\u4e00-\u9fa5a-zA-Z0-9·]{2,12}?(?:科技|技术|智能|机器人|半导体|芯片|能源|生物|医药|医疗|信息|网络|数据|云|软件|硬件|系统|集成|装备|制造|材料|光电|微电子|电子|通信|自动化|无人机|航天|航空|公司|集团|有限|股份))')

# 额外匹配“完成融资”句式中的公司名
FINANCE_PATTERN = re.compile(r'([\u4e00-\u9fa5a-zA-Z0-9·]{2,12}?)宣布|完成|获|融资|投资')

def extract_company_name(text):
    if not text:
        return None
    # 优先匹配公司后缀模式
    matches = COMPANY_PATTERN.findall(text)
    if matches:
        name = matches[0]
        # 去除地域前缀
        for prefix in ['深圳', '北京', '上海', '广州', '杭州', '成都', '武汉', '南京', '苏州', '天津', '重庆', '香港', '澳门']:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        return name.strip()
    # 如果上面没匹配，尝试匹配“完成融资”等句式
    matches2 = FINANCE_PATTERN.findall(text)
    if matches2:
        # 过滤掉常见的非公司词
        exclude = ['项目', '产品', '平台', '系统', '技术', '方案', '服务', '企业', '行业', '市场', '领域']
        for m in matches2:
            if len(m) >= 2 and m not in exclude:
                return m.strip()
    return None

# ====================== RSS 抓取函数 ======================
def fetch_rss_feed(url, max_entries=30):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        channel = root.find('channel')
        if channel is None:
            # Atom格式
            items = root.findall('entry')
            if not items:
                print(f"⚠️ {url} 未找到任何条目")
                return []
            articles = []
            for entry in items[:max_entries]:
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
        else:
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
    except Exception as e:
        print(f"⚠️ 抓取 RSS 失败: {url} - {e}")
        return []

# ====================== 公司信息生成（优化筛选条件） ======================
def build_company_from_article(article, source_name, strict=True):
    title = article.get('title', '')
    desc = article.get('description', '')
    link = article.get('link', '')
    pub_date = article.get('pub_date', '')
    
    # 组合文本用于提取
    full_text = title + " " + desc
    if len(full_text) < 5:
        return None
    
    # 提取公司名
    company_name = extract_company_name(title) or extract_company_name(desc)
    if not company_name:
        # 打印调试信息（会显示在Actions日志中）
        print(f"   ⚠️ 未提取到公司名: {title[:50]}...")
        return None
    print(f"   ✅ 提取到公司名: {company_name}")
    
    # 城市判断：只要文中出现中国主要城市即可（不再强制深圳）
    city_keywords = ['深圳', '广州', '东莞', '佛山', '香港', '澳门', '北京', '上海', '杭州', '成都', '武汉', '南京', '苏州', '天津', '重庆', '西安', '长沙', '郑州', '青岛', '大连', '厦门', '合肥', '济南', '福州']
    # 如果严格模式，必须包含深圳；宽松模式，包含任一城市即可
    if strict:
        is_location_ok = any(kw in title or kw in desc for kw in ['深圳'])
    else:
        is_location_ok = any(kw in title or kw in desc for kw in city_keywords)
    if not is_location_ok:
        print(f"   ⚠️ 城市不匹配: {company_name}")
        return None
    
    # 赛道判断：必须包含新兴行业关键词
    track_keywords = ['机器', '智能', '半导', '芯片', 'AI', '人工智', '低空', '无人', '新能源', '储能', '生物', '医药', '合成', '航天',
                      '科技', '技术', '软件', '硬件', '电子', '通信', '光电', '装备', '制造', '材料', '医疗', '健康', '环保', '能源']
    is_track = any(kw in title or kw in desc for kw in track_keywords)
    if not is_track:
        print(f"   ⚠️ 赛道不匹配: {company_name}")
        return None
    
    # 高成长判断：严格模式必须包含融资、投资等；宽松模式可接受合作、发布等
    if strict:
        growth_keywords = ['融资', '投资', '获', '完成', '亿元', '千万', '万美元']
    else:
        growth_keywords = ['融资', '投资', '增长', '扩张', '获', '完成', '亿元', '千万', '万美元', '战略', '合作', '发布', '推出', '量产', '基地', '签约', '落地']
    is_growth = any(kw in title or kw in desc for kw in growth_keywords)
    if not is_growth:
        print(f"   ⚠️ 成长性不匹配: {company_name}")
        return None
    
    # 排除头部企业
    blacklist = ['腾讯', '阿里', '百度', '华为', '字节', '美团', '京东', '网易', '小米', '拼多多', '滴滴', '大疆']
    if any(b in company_name for b in blacklist):
        print(f"   ⚠️ 头部企业已排除: {company_name}")
        return None
    
    # 构造公司字典
    dynamics = [f"{title}（来源：{source_name}）"]
    if link:
        dynamics.append(f"详情：{link}")
    
    # 赛道分类
    track = '其他'
    if any(kw in company_name or kw in title for kw in ['机器', '智能']):
        track = '具身智能/机器人'
    elif any(kw in company_name or kw in title for kw in ['半导', '芯片']):
        track = '半导体'
    elif any(kw in company_name or kw in title for kw in ['AI', '人工智']):
        track = '人工智能'
    elif any(kw in company_name or kw in title for kw in ['低空', '无人']):
        track = '低空经济'
    elif any(kw in company_name or kw in title for kw in ['新能源', '储能']):
        track = '新能源'
    elif any(kw in company_name or kw in title for kw in ['生物', '医药', '合成']):
        track = '生物医药'
    elif any(kw in company_name or kw in title for kw in ['科技', '软件', '硬件']):
        track = '科技'
    elif any(kw in company_name or kw in title for kw in ['制造', '装备']):
        track = '制造'
    
    # 发展阶段
    if '融资' in title or '融资' in desc:
        stage = '快速扩张期'
    elif 'IPO' in title or '上市' in title:
        stage = 'IPO冲刺期'
    elif '合作' in title or '合作' in desc:
        stage = '战略合作期'
    elif '发布' in title or '发布' in desc:
        stage = '产品发布期'
    else:
        stage = '成长期'
    
    # 城市信息
    branches = '推测'
    for city in ['深圳', '北京', '上海', '广州', '杭州']:
        if city in title or city in desc:
            branches = city
            break
    if branches == '推测':
        branches = '中国'
    
    return {
        "name": company_name,
        "track": track,
        "employees": '未知',
        "finance": '',
        "branches": branches,
        "rd_ratio": '',
        "honor": '',
        "stage": stage,
        "dynamics": dynamics
    }

# ====================== 抓取主函数 ======================
def fetch_companies_from_rss(strict=True):
    all_companies = []
    seen_names = set()
    mode = "严格" if strict else "宽松"
    print(f"🔍 开始 {mode} 抓取...")
    for source in RSS_SOURCES:
        articles = fetch_rss_feed(source['url'])
        print(f"📡 {source['name']} 抓取到 {len(articles)} 篇文章")
        for article in articles:
            company = build_company_from_article(article, source['name'], strict=strict)
            if company and company['name'] not in seen_names:
                seen_names.add(company['name'])
                all_companies.append(company)
                print(f"   🎯 通过筛选: {company['name']}")
        time.sleep(1)
    print(f"✅ {mode} 抓取完成，共 {len(all_companies)} 家合格公司")
    return all_companies

# ====================== 手动保底名单（仅作为最后保底，已大幅减少） ======================
MANUAL_COMPANIES = [
    {
        "name": "逐际动力",
        "track": "具身智能",
        "employees": "快速扩张中",
        "finance": "Pre-IPO轮近2亿美元",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "",
        "stage": "Pre-IPO冲刺期",
        "dynamics": ["2026年7月14日完成近2亿美元Pre-IPO轮融资（来源：新华社）"]
    },
    {
        "name": "埃芯半导体",
        "track": "半导体",
        "employees": "近300人（研发占60%）",
        "finance": "B+轮近10亿元",
        "branches": "深圳",
        "rd_ratio": "60%",
        "honor": "国家级专精特新小巨人",
        "stage": "快速扩张期",
        "dynamics": ["2026年7月29日完成近10亿元B+轮融资（来源：投资界）"]
    }
]

# ====================== 主入口 ======================
def get_all_companies():
    # 先严格抓取
    strict_companies = fetch_companies_from_rss(strict=True)
    # 如果严格抓取 >= 6 家，直接返回前8家
    if len(strict_companies) >= 6:
        return strict_companies[:8]
    
    # 否则宽松抓取
    loose_companies = fetch_companies_from_rss(strict=False)
    
    # 合并去重
    combined = strict_companies.copy()
    existing_names = set(c['name'] for c in combined)
    for comp in loose_companies:
        if comp['name'] not in existing_names:
            combined.append(comp)
            existing_names.add(comp['name'])
    
    # 如果合并后仍少于6家，用少量保底
    if len(combined) < 6:
        for manual in MANUAL_COMPANIES:
            if manual['name'] not in existing_names:
                combined.append(manual)
                existing_names.add(manual['name'])
            if len(combined) >= 6:
                break
    return combined[:8]

COMPANIES = get_all_companies()
