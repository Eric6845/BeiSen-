# -*- coding: utf-8 -*-
import os
import json
import random
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ====================== RSS 数据源配置 ======================
RSS_SOURCES = [
    {"name": "36氪_投融资", "url": "https://36kr.com/feed", "type": "rss"},
    {"name": "投资界", "url": "https://pe.pedaily.cn/rss/", "type": "rss"},
    {"name": "量子位", "url": "https://www.qbitai.com/feed", "type": "rss"},
    {"name": "动点科技", "url": "https://www.technode.com/feed", "type": "rss"},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss", "type": "rss"}
]

# ====================== 公司名提取工具 ======================
COMPANY_SUFFIX = r'(?:科技|技术|智能|机器人|半导体|芯片|能源|生物|医药|医疗|信息|网络|数据|云|软件|硬件|系统|集成|装备|制造|材料|光电|微电子|电子|通信|自动化|无人机|航天|航空)'
COMPANY_PATTERN = re.compile(r'([\u4e00-\u9fa5a-zA-Z0-9·]{2,10}?(?:' + COMPANY_SUFFIX + r'|公司|集团|有限|股份|有限公|集团有限))')

def extract_company_name(text):
    if not text:
        return None
    matches = COMPANY_PATTERN.findall(text)
    if matches:
        name = matches[0]
        for prefix in ['深圳', '北京', '上海', '广州', '杭州', '成都', '武汉', '南京', '苏州']:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        return name.strip()
    return None

# ====================== RSS 抓取函数 ======================
def fetch_rss_feed(url, max_entries=20):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        ns = {'': ''}
        channel = root.find('channel')
        if channel is None:
            items = root.findall('entry')
            if not items:
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

# ====================== 公司信息生成（含严格/宽松模式） ======================
def build_company_from_article(article, source_name, strict=True):
    title = article.get('title', '')
    desc = article.get('description', '')
    link = article.get('link', '')
    pub_date = article.get('pub_date', '')
    
    company_name = extract_company_name(title) or extract_company_name(desc)
    if not company_name:
        return None
    
    # 城市判断
    if strict:
        is_location_ok = '深圳' in title or '深圳' in desc or '深圳' in company_name
    else:
        location_keywords = ['深圳', '广州', '东莞', '佛山', '香港', '澳门', '北京', '上海', '杭州', '成都', '武汉', '南京', '苏州', '天津', '重庆']
        is_location_ok = any(kw in title or kw in desc or kw in company_name for kw in location_keywords)
    if not is_location_ok:
        return None
    
    # 赛道判断
    if strict:
        track_keywords = ['机器', '智能', '半导', '芯片', 'AI', '人工智', '低空', '无人', '新能源', '储能', '生物', '医药', '合成', '航天']
    else:
        track_keywords = ['机器', '智能', '半导', '芯片', 'AI', '人工智', '低空', '无人', '新能源', '储能', '生物', '医药', '合成', '航天',
                          '科技', '技术', '软件', '硬件', '电子', '通信', '光电', '装备', '制造', '材料', '医疗', '健康', '环保', '能源']
    is_track = any(kw in title or kw in desc for kw in track_keywords)
    if not is_track:
        return None
    
    # 高成长判断
    if strict:
        growth_strict = ['融资', '投资', '获', '完成', '亿元', '千万', '万美元']
        is_growth = any(kw in title or kw in desc for kw in growth_strict)
    else:
        growth_keywords = ['融资', '投资', '增长', '扩张', '获', '完成', '亿元', '千万', '万美元', '战略', '合作', '发布', '推出', '量产', '基地', '签约', '落地']
        is_growth = any(kw in title or kw in desc for kw in growth_keywords)
    if not is_growth:
        return None
    
    # 排除头部
    blacklist = ['腾讯', '阿里', '百度', '华为', '字节', '美团', '京东', '网易', '小米', '拼多多', '滴滴', '大疆']
    if any(b in company_name for b in blacklist):
        return None
    
    # 构造公司字典
    dynamics = [f"{title}（来源：{source_name}）"]
    if link:
        dynamics.append(f"详情：{link}")
    
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
    
    employees = '未知'
    finance = ''
    branches = '推测'
    if '深圳' in title or '深圳' in desc:
        branches = '深圳'
    elif any(kw in title or kw in desc for kw in ['广州', '东莞', '佛山']):
        branches = '粤港澳大湾区'
    
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
    
    return {
        "name": company_name,
        "track": track,
        "employees": employees,
        "finance": finance,
        "branches": branches,
        "rd_ratio": "",
        "honor": "",
        "stage": stage,
        "dynamics": dynamics
    }

# ====================== 抓取 RSS 并返回公司列表（支持严格/宽松） ======================
def fetch_companies_from_rss(strict=True):
    all_companies = []
    seen_names = set()
    for source in RSS_SOURCES:
        articles = fetch_rss_feed(source['url'])
        mode = "严格" if strict else "宽松"
        print(f"📡 {source['name']} ({mode}) 抓取到 {len(articles)} 篇文章")
        for article in articles:
            company = build_company_from_article(article, source['name'], strict=strict)
            if company and company['name'] not in seen_names:
                seen_names.add(company['name'])
                all_companies.append(company)
        time.sleep(1)
    return all_companies

# ====================== 手动保底名单 ======================
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
        "dynamics": [
            "2026年7月14日完成近2亿美元Pre-IPO轮融资（来源：新华社）",
            "半年内累计吸金4亿美元（来源：36氪）",
            "加速人形机器人商业化落地（来源：公司官网）",
            "与多家车企达成战略合作（来源：猎豹资讯）"
        ]
    },
    {
        "name": "埃芯半导体",
        "track": "半导体",
        "employees": "近300人（研发占60%）",
        "finance": "B+轮近10亿元",
        "branches": "深圳/西安/惠州",
        "rd_ratio": "60%",
        "honor": "国家级专精特新小巨人",
        "stage": "快速扩张期",
        "dynamics": [
            "2026年7月29日完成近10亿元B+轮融资（来源：投资界）",
            "累计出货突破100台（来源：公司官网）",
            "西安研发中心正式启用（来源：陕西日报）",
            "获评国家级专精特新重点小巨人（来源：工信部）"
        ]
    },
    {
        "name": "智平方",
        "track": "具身智能",
        "employees": "快速扩张中",
        "finance": "估值超200亿元",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "新晋独角兽",
        "stage": "高速融资扩张期",
        "dynamics": [
            "2026年6月完成近50亿元融资（来源：投资者网）",
            "一年内完成12轮融资（来源：36氪）",
            "成为大湾区首个200亿具身智能独角兽（来源：南方日报）"
        ]
    }
]

# ====================== 主数据源函数：智能宽松 ======================
def get_all_companies():
    strict_companies = fetch_companies_from_rss(strict=True)
    print(f"✅ 严格抓取到 {len(strict_companies)} 家合格公司")
    if len(strict_companies) >= 6:
        return strict_companies[:8]
    
    loose_companies = fetch_companies_from_rss(strict=False)
    print(f"✅ 宽松抓取到 {len(loose_companies)} 家合格公司")
    
    combined = strict_companies.copy()
    existing_names = set(c['name'] for c in combined)
    for comp in loose_companies:
        if comp['name'] not in existing_names:
            combined.append(comp)
            existing_names.add(comp['name'])
    
    if len(combined) < 6:
        for manual in MANUAL_COMPANIES:
            if manual['name'] not in existing_names:
                combined.append(manual)
                existing_names.add(manual['name'])
            if len(combined) >= 8:
                break
    return combined[:8]

COMPANIES = get_all_companies()

# ====================== 痛点匹配 ======================
def match_pain_point(company):
    name = company["name"]
    finance = company.get("finance", "")
    stage = company.get("stage", "")
    rd = company.get("rd_ratio", "")
    branches = company.get("branches", "")
    honor = company.get("honor", "")

    if any(kw in stage or kw in finance for kw in ["IPO", "上市", "股改", "Pre-IPO", "递表", "受理", "辅导"]):
        return {
            "type": "IPO合规管理刚需",
            "desc": f"贵公司正处于IPO关键期【{stage}】，上市合规对人力资源管理有严格要求——招聘流程可追溯、绩效数据可审计、薪酬体系规范化。北森已服务多家上市企业，可提供合规级HR管理方案。"
        }
    if "融资" in finance or "估值" in finance or "融资" in stage:
        return {
            "type": "融资后快速扩张，组织管理跟不上",
            "desc": f"贵公司近期完成融资【{finance}】，员工规模快速扩张——组织层级从扁平变成多级。北森一体化HCM平台，让组织调整在系统内分钟级完成。"
        }
    if rd and "研发" in rd or "半导" in company.get("track", ""):
        return {
            "type": "研发驱动型，人才争夺激烈",
            "desc": f"贵公司【{rd if rd else '高比例'}】是研发人员——在深圳激烈的人才争夺战中，北森从招聘到绩效到发展的全链路人才管理，帮您系统性打赢人才战。"
        }
    if "/" in branches or "全球" in branches or "多国" in branches:
        return {
            "type": "多地域/全球化布局",
            "desc": f"贵公司在{branches}多地布局——北森全球人力一体化方案，支持多语言、多时区、多币种，一套系统管全球。"
        }
    if "最佳雇主" in honor:
        return {
            "type": "最佳雇主认证，HR体系升级需求",
            "desc": "恭喜贵公司荣获'最佳雇主'称号！北森一体化HCM平台帮您把人才管理的理念落地为系统化的制度与数据。"
        }
    return {
        "type": "组织管理数字化升级",
        "desc": f"贵公司处于{stage}，员工规模持续增长。北森一体化HCM平台可帮助企业实现人力资源全链路数字化管理。"
    }

# ====================== 动态选取（基于日期种子） ======================
def get_today_dynamic(company):
    today = datetime.now()
    seed = today.year * 10000 + today.month * 100 + today.day
    name_hash = sum([ord(c) for c in company["name"]])
    dyn_list = company.get("dynamics", [])
    if not dyn_list:
        return "暂无动态"
    idx = (seed + name_hash) % len(dyn_list)
    return dyn_list[idx]

# ====================== 生成HTML日报 ======================
def generate_html_report():
    today_str = datetime.now().strftime("%Y年%m月%d日")
    s_list, a_list, b_list = [], [], []

    all_companies = get_all_companies()  # 实时获取，保证最新

    if not all_companies:
        return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>北森拓客日报</title></head>
<body style="font-family:Arial;text-align:center;padding:50px;">
<h1>📋 北森拓客日报</h1>
<p style="color:#64748b;">{today_str}</p>
<p style="font-size:18px;color:#3b82f6;">今日暂无符合条件的动态更新，请明天再查看。</p>
<p style="color:#94a3b8;font-size:14px;">数据源：RSS抓取 + 手动维护</p>
</body>
</html>
"""

    for comp in all_companies:
        dynamic = get_today_dynamic(comp)
        pain = match_pain_point(comp)
        comp["today_dynamic"] = dynamic
        comp["pain_point"] = pain

        if any(kw in dynamic for kw in ["融资", "IPO", "上市", "递表", "受理", "辅导", "Pre-IPO"]):
            s_list.append(comp)
        elif any(kw in dynamic for kw in ["合作", "扩张", "量产", "发布", "基地", "获奖"]):
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
<div class="stat-item"><div class="num">{len(all_companies)}</div><div class="label">📊 总企业数</div></div>
</div>
"""

    for level, items, label in [("s", s_list, "S级 · 重大动态（融资/IPO进展）"),
                                ("a", a_list, "A级 · 近期动态（合作/扩张/发布）"),
                                ("b", b_list, "B级 · 关注中")]:
        if items:
            html += f'<div class="section section-{level}"><div class="section-title">{"🔴" if level=="s" else "🟡" if level=="a" else "🔵"} {label}</div>'
            for comp in items:
                pain = comp["pain_point"]
                html += f"""
<div class="card card-{level}">
<div class="card-header"><span class="card-name">{comp['name']}</span><span class="card-tag">{comp['track']}</span></div>
<div class="card-info"><span>👥 {comp['employees']}</span><span>💰 {comp['finance']}</span><span>📍 {comp['branches']}</span><span class="card-stage">📌 {comp['stage']}</span></div>
<div class="card-dynamic">📰 {comp['today_dynamic']}</div>
<div class="card-pain"><div class="ptype">💡 核心痛点：{pain['type']}</div><div class="pdesc">🎯 切入点：{pain['desc']}</div></div>
</div>
"""
            html += '</div>'

    html += f"""
<div class="footer">数据来源：公开新闻报道（36氪、投资界、量子位等）<br>本日报由自动化系统生成，仅供内部业务拓展参考</div>
</div>
</body>
</html>
"""
    return html

# ====================== 主程序 ======================
if __name__ == "__main__":
    html_content = generate_html_report()
    filename = "index.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 日报已生成：{filename}")
    print(f"📊 共 {len(COMPANIES)} 家企业")
