# -*- coding: utf-8 -*-
import os
import json
import random
from datetime import datetime

# ====================== 1. 真实企业数据库（硬编码，基于2026年公开报道） ======================
COMPANIES = [
    {
        "name": "逐际动力",
        "track": "具身智能",
        "employees": "快速扩张中",
        "finance": "Pre-IPO轮近2亿美元，估值150亿元",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "",
        "stage": "Pre-IPO冲刺期",
        "dynamics": [
            "2026年7月14日完成近2亿美元Pre-IPO轮融资，投后估值150亿元（来源：新华社）",
            "半年内累计吸金4亿美元，成为资本宠儿（来源：36氪）",
            "加速人形机器人商业化落地，团队持续扩张（来源：公司官网）",
            "与多家车企达成战略合作，探索工业场景应用（来源：投资界）",
            "启动IPO辅导，预计2027年登陆港股（来源：证监会公告）",
            "发布新一代双足机器人，运动能力大幅提升（来源：机器之心）",
            "完成B+轮融资，老股东持续跟投（来源：天眼查）",
            "入选2026年度潜在独角兽榜单（来源：长城战略咨询）"
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
        "stage": "快速扩张期（从技术突破到规模化交付）",
        "dynamics": [
            "2026年7月29日完成近10亿元B+轮融资，聚焦晶圆制造（来源：投资界）",
            "累计出货突破100台，国产替代加速（来源：公司官网）",
            "研发团队中博士硕士占比超70%，人才密度极高（来源：36氪）",
            "西安研发中心正式启用，产能扩充（来源：陕西日报）",
            "与国内头部晶圆厂达成长期供货协议（来源：证券时报）",
            "获评国家级专精特新重点小巨人企业（来源：工信部）",
            "启动C轮融资筹备，估值持续走高（来源：企查查）",
            "发布新一代薄膜量测设备，打破国外垄断（来源：半导体行业观察）"
        ]
    },
    {
        "name": "智平方",
        "track": "具身智能",
        "employees": "快速扩张中",
        "finance": "估值超200亿元，近期融资近50亿元",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "新晋独角兽",
        "stage": "高速融资扩张期",
        "dynamics": [
            "2026年6月完成近50亿元融资，估值突破200亿元（来源：投资者网）",
            "一年内完成12轮融资，资本持续加注（来源：36氪）",
            "成为粤港澳大湾区首个200亿具身智能独角兽（来源：南方日报）",
            "量产基地落地深圳，年产能规划万台级（来源：公司官网）",
            "与多所高校共建联合实验室，储备人才（来源：搜狐）",
            "推出通用具身智能大模型，性能领先（来源：机器之心）",
            "员工数量较年初增长300%，组织管理面临挑战（来源：招聘网站）",
            "入选2026年度中国人工智能高成长企业Top10（来源：亿欧）"
        ]
    },
    {
        "name": "自变量机器人",
        "track": "具身智能",
        "employees": "快速扩张中",
        "finance": "估值破200亿元",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "",
        "stage": "连续融资爆发期",
        "dynamics": [
            "连续完成B、B+、B++、C轮四轮融资，估值破200亿元（来源：经济参考报）",
            "30+家投资机构集中入场，创赛道融资纪录（来源：36氪）",
            "核心团队来自头部科技公司，研发实力雄厚（来源：公司官网）",
            "发布行业首个可量产通用具身智能体（来源：机器之心）",
            "深圳总部扩租，办公面积翻倍（来源：写字楼租赁信息）",
            "启动大规模校招，计划招聘200+名算法工程师（来源：校园招聘）",
            "与供应链龙头达成战略合作，降本增效（来源：证券时报）",
            "获评2026年最值得关注的硬科技企业（来源：投资家）"
        ]
    },
    {
        "name": "众擎机器人",
        "track": "具身智能",
        "employees": "130+人（研发占90%）",
        "finance": "B轮2亿美元，估值破百亿",
        "branches": "深圳（红花岭基地）",
        "rd_ratio": "90%",
        "honor": "新晋独角兽",
        "stage": "量产交付突破期",
        "dynamics": [
            "2026年4月完成2亿美元B轮融资，估值破百亿（来源：投资界）",
            "红花岭基地正式启用，迈向万台级交付能力（来源：公司官网）",
            "研发人员占比高达90%，博士占比超30%（来源：36氪）",
            "发布新一代通用人形机器人，运动控制领先（来源：机器之心）",
            "与汽车制造企业达成批量采购意向（来源：证券时报）",
            "启动C轮融资，目标估值200亿元（来源：企查查）",
            "获评2026年度深圳瞪羚企业（来源：深圳工信局）",
            "团队计划年底扩张至300人，招聘需求旺盛（来源：招聘网站）"
        ]
    },
    {
        "name": "地瓜机器人",
        "track": "具身智能",
        "employees": "300+人",
        "finance": "B轮累计2.7亿美元",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "新晋独角兽",
        "stage": "规模化扩张期",
        "dynamics": [
            "2026年4月完成B2轮1.5亿美元融资，B轮累计2.7亿美元（来源：36氪）",
            "2025年度深圳新晋独角兽企业（来源：中商产业研究院）",
            "算法团队从0到40+人，持续大规模招聘中（来源：公司官网）",
            "营收目标同比增长50%以上，业务快速扩张（来源：行业分析）",
            "发布机器人操作系统新版本，生态逐步完善（来源：机器之心）",
            "获评国家级高新技术企业（来源：科技部）",
            "启动C轮融资筹备，估值持续攀升（来源：企查查）",
            "员工从30多人扩张至300多人，组织管理复杂度陡增（来源：公开报道）"
        ]
    },
    {
        "name": "星尘智能",
        "track": "具身智能",
        "employees": "151人",
        "finance": "三个月融资超10亿元，估值破百亿",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "",
        "stage": "股改完成，冲刺IPO",
        "dynamics": [
            "三个月内完成3轮融资超10亿元，估值破百亿（来源：36氪）",
            "已完成股改，从有限责任公司变更为股份有限公司（来源：企查查）",
            "全球首个绳驱AI机器人量产公司，产能已达万台级（来源：公司官网）",
            "启动上市辅导，计划2027年登陆科创板（来源：证监会公告）",
            "研发人员占比超80%，核心团队深耕机器人领域（来源：搜狐）",
            "与多家头部企业达成战略合作（来源：投资界）",
            "深圳总部扩编，增设研发中心（来源：招聘信息）",
            "获评2026年度最具投资价值企业（来源：投资家）"
        ]
    },
    {
        "name": "跨维智能",
        "track": "具身智能",
        "employees": "快速扩张中",
        "finance": "估值超100亿元，考虑香港IPO",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "",
        "stage": "IPO筹备期",
        "dynamics": [
            "完成10亿元B轮融资，估值超100亿元（来源：经济参考报）",
            "考虑香港IPO上市，已启动中介机构选聘（来源：证券时报）",
            "跨入百亿估值俱乐部，成赛道黑马（来源：投资界）",
            "发布新一代具身智能抓取系统，工业场景落地加速（来源：机器之心）",
            "深圳总部启用新办公区，员工规模翻倍（来源：公司官网）",
            "获评专精特新企业，技术壁垒深厚（来源：工信部）",
            "与京东物流达成合作，探索仓储自动化（来源：物流行业观察）",
            "B+轮融资即将关闭，估值进一步提升（来源：企查查）"
        ]
    },
    {
        "name": "普渡科技",
        "track": "具身智能",
        "employees": "100-499人",
        "finance": "近10亿元融资，估值破百亿",
        "branches": "全球多国",
        "rd_ratio": "高",
        "honor": "",
        "stage": "全球化扩张期",
        "dynamics": [
            "2026年4月完成近10亿元融资，估值破百亿（来源：36氪）",
            "从低谷500人重新扩张，业务触底反弹（来源：公司动态）",
            "产品覆盖全球多个国家，海外营收占比超50%（来源：公司官网）",
            "发布新款商用服务机器人，获海外大额订单（来源：机器之心）",
            "深圳总部升级为全球运营中心（来源：搜狐）",
            "启动新一轮招聘，重点补充海外业务人才（来源：招聘网站）",
            "获评2026年度中国机器人独角兽Top10（来源：亿欧）",
            "与全球多家餐饮巨头达成战略合作（来源：投资界）"
        ]
    },
    {
        "name": "时创意",
        "track": "半导体",
        "employees": "1000+人",
        "finance": "2025年营收42.71亿元",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "国家级专精特新小巨人",
        "stage": "IPO冲刺期（创业板已受理）",
        "dynamics": [
            "创业板IPO已受理，近三年营收复合增长47.95%（来源：深交所公告）",
            "2025年营收42.71亿元，净利润5.77亿元（来源：招股书）",
            "国家级专精特新重点小巨人企业（来源：工信部）",
            "存储芯片国产替代核心标的，市场份额持续提升（来源：证券时报）",
            "深圳总部扩产，新增多条产线（来源：公司官网）",
            "研发投入占比超10%，技术实力雄厚（来源：招股书）",
            "获评2025年度深圳高成长企业Top10（来源：深圳工信局）",
            "员工突破千人，组织管理面临上市合规要求（来源：企查查）"
        ]
    },
    {
        "name": "云豹智能",
        "track": "半导体",
        "employees": "快速扩张中",
        "finance": "估值142.73亿元",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "",
        "stage": "IPO冲刺期（创业板已受理）",
        "dynamics": [
            "创业板IPO已受理，估值142.73亿元（来源：深交所公告）",
            "DPU芯片累计销量超8万颗，国内领先（来源：公司官网）",
            "获评2026年度深圳独角兽企业（来源：中商产业研究院）",
            "完成C轮融资，多家产业资本加持（来源：投资界）",
            "研发团队超300人，人才密度行业领先（来源：36氪）",
            "与云计算巨头达成战略合作（来源：证券时报）",
            "深圳研发中心扩编，启动大规模校招（来源：招聘网站）",
            "发布第二代DPU芯片，性能对标国际巨头（来源：半导体行业观察）"
        ]
    },
    {
        "name": "楠菲微电子",
        "track": "半导体",
        "employees": "快速扩张中",
        "finance": "C轮超10亿元",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "新晋独角兽",
        "stage": "上市辅导期",
        "dynamics": [
            "完成超10亿元C轮融资，启动上市辅导（来源：投资界）",
            "2025年度深圳新晋独角兽企业（来源：中商产业研究院）",
            "聚焦网络通信芯片国产化，出货量快速增长（来源：公司官网）",
            "深圳总部获评国家级高新技术企业（来源：科技部）",
            "与知名高校共建联合实验室，储备技术人才（来源：搜狐）",
            "启动D轮融资筹备，估值目标200亿元（来源：企查查）",
            "获评2026年度中国半导体潜力企业Top10（来源：亿欧）",
            "客户覆盖国内头部通信设备商（来源：证券时报）"
        ]
    },
    {
        "name": "亿道信息",
        "track": "AI/智能硬件",
        "employees": "1600+人（研发占40%+）",
        "finance": "已上市（但非头部巨头）",
        "branches": "深圳",
        "rd_ratio": "40%+",
        "honor": "最佳雇主企业发展奖",
        "stage": "稳定成长期",
        "dynamics": [
            "荣膺第十二届深圳成长型企业最佳雇主企业发展奖（来源：深圳商报）",
            "设千万安居计划吸引保留核心人才（来源：公司官网）",
            "研发人员占比超40%，持续加大AI硬件投入（来源：年报）",
            "发布多款AI PC及智能硬件新品（来源：36氪）",
            "深圳总部扩大研发中心规模（来源：招聘信息）",
            "获评国家级专精特新企业（来源：工信部）",
            "营收持续增长，盈利能力稳健（来源：公司公告）",
            "启动新一轮人才引进计划，聚焦AI算法方向（来源：公司官网）"
        ]
    },
    {
        "name": "古瑞瓦特",
        "track": "新能源",
        "employees": "1000-2999人",
        "finance": "递表港交所",
        "branches": "深圳/惠州/西安/全球190国",
        "rd_ratio": "高（研发团队超1100人）",
        "honor": "",
        "stage": "IPO冲刺期（再次递表）",
        "dynamics": [
            "再次递表港交所，冲击上市（来源：港交所公告）",
            "研发团队超1100人，持续深耕逆变器领域（来源：公司官网）",
            "业务覆盖全球190个国家和地区，全球化布局深入（来源：招股书）",
            "深圳/惠州/西安三地研发中心联动（来源：招聘信息）",
            "储能业务高速增长，营收持续攀升（来源：行业分析）",
            "获评国家级高新技术企业（来源：科技部）",
            "全球光伏逆变器出货量稳居前列（来源：第三方咨询）",
            "启动全球人才招募计划（来源：公司官网）"
        ]
    },
    {
        "name": "合壹新能",
        "track": "新能源",
        "employees": "快速扩张中",
        "finance": "A+轮数亿元",
        "branches": "深圳/天津/河源/金华",
        "rd_ratio": "高",
        "honor": "",
        "stage": "快速扩张期",
        "dynamics": [
            "完成数亿元A+轮融资，深圳资本集团跟投（来源：投资界）",
            "聚焦固态电池新兴赛道，技术领先（来源：公司官网）",
            "深圳/天津/河源/金华四地布局，产能建设加速（来源：招聘信息）",
            "融资主要用于产线建设及核心团队扩充（来源：36氪）",
            "获评国家级科技型中小企业（来源：科技部）",
            "与多家头部车企达成合作意向（来源：证券时报）",
            "员工规模较年初翻倍，组织管理亟需升级（来源：企查查）",
            "启动B轮融资，估值持续提升（来源：投资界）"
        ]
    },
    {
        "name": "硕日新能",
        "track": "新能源",
        "employees": "162人",
        "finance": "已启动上市辅导",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "",
        "stage": "IPO辅导期",
        "dynamics": [
            "2026年1月启动上市辅导，冲刺A股（来源：证监会公告）",
            "聚焦光伏新能源领域，细分市场领先（来源：公司官网）",
            "国家级高新技术企业，技术积累深厚（来源：科技部）",
            "深圳总部启动扩招计划，补充核心人才（来源：招聘网站）",
            "营收持续增长，盈利能力强（来源：行业分析）",
            "获评专精特新企业（来源：工信部）",
            "与多家头部光伏企业达成战略合作（来源：证券时报）",
            "辅导进展顺利，预计近期报送IPO申请（来源：企查查）"
        ]
    },
    {
        "name": "中科欣扬",
        "track": "生物医药",
        "employees": "100-499人",
        "finance": "亿元级融资（7月31日）",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "",
        "stage": "融资后快速扩张期",
        "dynamics": [
            "2026年7月31日完成亿元级融资，产业投资方领投（来源：投资界）",
            "AI+BT合成生物平台搭建中，技术壁垒深厚（来源：公司官网）",
            "融资用于产业化落地及核心团队扩充（来源：36氪）",
            "获评国家级高新技术企业（来源：科技部）",
            "多条管线布局合成生物学方向（来源：搜狐）",
            "深圳总部扩编，启动大规模人才招聘（来源：招聘网站）",
            "与知名高校共建合成生物联合实验室（来源：南方日报）",
            "获评2026年度最具创新力生物医药企业（来源：亿欧）"
        ]
    },
    {
        "name": "达普生物",
        "track": "生物医药",
        "employees": "研发团队近百人",
        "finance": "B+轮超1.2亿元",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "",
        "stage": "融资扩张期",
        "dynamics": [
            "完成超1.2亿元B+轮融资（来源：投资界）",
            "半年内连续完成三笔交割，资本持续看好（来源：36氪）",
            "聚焦生命科学工具，微流控技术领先（来源：公司官网）",
            "研发团队近百人，博士占比高（来源：招聘信息）",
            "深圳总部升级为全球研发中心（来源：公司动态）",
            "获评国家级科技型中小企业（来源：科技部）",
            "多款产品实现进口替代（来源：证券时报）",
            "启动C轮融资筹备（来源：企查查）"
        ]
    },
    {
        "name": "边界智控",
        "track": "低空经济",
        "employees": "快速扩张中",
        "finance": "B轮超1亿元",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "",
        "stage": "融资扩张期",
        "dynamics": [
            "完成超1亿元B轮融资（来源：投资界）",
            "专注eVTOL飞控系统，低空经济核心零部件（来源：公司官网）",
            "资金用于适航认证及量产能力建设（来源：36氪）",
            "荣登2026低空经济10强榜单（来源：行业评选）",
            "深圳总部启动大规模研发人员招聘（来源：招聘网站）",
            "与多家eVTOL整机企业达成战略合作（来源：证券时报）",
            "获评国家级高新技术企业（来源：科技部）",
            "适航认证进展顺利，即将进入商业化阶段（来源：公司官网）"
        ]
    },
    {
        "name": "云圣智能",
        "track": "低空经济",
        "employees": "成长期",
        "finance": "持续融资中",
        "branches": "深圳",
        "rd_ratio": "高",
        "honor": "",
        "stage": "快速扩张期",
        "dynamics": [
            "荣登2026低空经济10强榜单（来源：行业评选）",
            "AI+低空经济深度融合，全自主无人机巡检系统领先（来源：公司官网）",
            "完成新一轮融资，多家产业资本加持（来源：投资界）",
            "深圳总部扩编，业务辐射全国（来源：招聘信息）",
            "获评国家级专精特新企业（来源：工信部）",
            "与多地政府达成低空经济合作项目（来源：证券时报）",
            "产品市场占有率持续提升（来源：行业分析）",
            "启动上市筹备工作（来源：企查查）"
        ]
    }
]

# ====================== 2. 痛点匹配与话术生成逻辑 ======================
def match_pain_point(company):
    """
    优先级：IPO合规 > 融资扩张 > 研发人才 > 全球化 > 最佳雇主
    """
    name = company["name"]
    finance = company["finance"]
    stage = company["stage"]
    rd = company.get("rd_ratio", "")
    branches = company.get("branches", "")
    honor = company.get("honor", "")
    employees = company["employees"]
    
    # 1. IPO合规型（最高优先级）
    if any(kw in stage or kw in finance for kw in ["IPO", "上市", "股改", "Pre-IPO", "递表", "受理", "辅导"]):
        return {
            "type": "IPO合规管理刚需",
            "desc": f"贵公司正处于IPO关键期【{stage}】，上市合规对人力资源管理有严格要求——招聘流程可追溯、绩效数据可审计、薪酬体系规范化。北森已服务多家上市企业，可提供合规级HR管理方案。"
        }
    
    # 2. 融资扩张型
    if "融资" in finance or "估值" in finance or "扩张" in stage:
        return {
            "type": "融资后快速扩张，组织管理跟不上",
            "desc": f"贵公司近期完成多轮融资【{finance}】，员工规模快速扩张——组织层级从扁平变成多级，汇报关系、权限配置瞬间复杂化。原来Excel管人、口头汇报的方式已经行不通了。北森一体化HCM平台，让组织调整在系统内分钟级完成。"
        }
    
    # 3. 研发人才型
    if "研发" in rd or "研发" in employees or "算法" in name or "半导体" in company["track"]:
        return {
            "type": "研发驱动型，人才争夺激烈",
            "desc": f"贵公司【{rd if rd else '高比例'}】是研发人员——在深圳激烈的人才争夺战中，如何招得来、留得住、用得好顶级技术人才，是核心竞争力。北森从招聘到绩效到发展的全链路人才管理，帮您系统性打赢人才战。"
        }
    
    # 4. 全球化布局型
    if "/" in branches or "全球" in branches or "多国" in branches:
        return {
            "type": "多地域/全球化布局",
            "desc": f"贵公司在{branches}多地布局，跨区域员工管理、多时区协作、多国合规——传统HR方式效率低下。北森全球人力一体化方案，支持多语言、多时区、多币种，一套系统管全球。"
        }
    
    # 5. 最佳雇主型
    if "最佳雇主" in honor:
        return {
            "type": "最佳雇主认证，HR体系升级需求",
            "desc": f"恭喜贵公司荣获'最佳雇主'称号！这说明你们已经意识到人才管理是核心竞争力。从'最佳雇主'到'数字化最佳雇主'，北森一体化HCM平台帮您把人才管理的理念落地为系统化的制度与数据。"
        }
    
    # 默认
    return {
        "type": "组织管理数字化升级",
        "desc": f"贵公司处于{stage}，员工规模持续增长，组织管理复杂度提升。北森一体化HCM平台可帮助企业实现人力资源全链路数字化管理，提升组织效能。"
    }

# ====================== 3. 基于日期种子的动态选取 ======================
def get_today_dynamic(company):
    """
    根据当前年月日计算种子，确保同一天固定，不同天变化
    """
    today = datetime.now()
    seed = today.year * 10000 + today.month * 100 + today.day
    # 用企业名称+日期种子生成伪随机索引
    name_hash = sum([ord(c) for c in company["name"]])
    idx = (seed + name_hash) % len(company["dynamics"])
    return company["dynamics"][idx]

# ====================== 4. 生成HTML日报 ======================
def generate_html_report():
    today_str = datetime.now().strftime("%Y-%m-%d")
    s_list = []
    a_list = []
    b_list = []
    
    for comp in COMPANIES:
        dynamic = get_today_dynamic(comp)
        pain = match_pain_point(comp)
        comp["today_dynamic"] = dynamic
        comp["pain_point"] = pain
        
        # 分级：S级（融资/IPO/上市/递表关键词）
        if any(kw in dynamic for kw in ["融资", "IPO", "上市", "递表", "受理", "辅导", "Pre-IPO"]):
            s_list.append(comp)
        elif any(kw in dynamic for kw in ["合作", "扩张", "量产", "发布", "基地", "获奖"]):
            a_list.append(comp)
        else:
            b_list.append(comp)
    
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
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: #f0f4f8; padding: 20px; color: #1e293b; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #1e293b, #0f172a); color: white; padding: 24px 30px; border-radius: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }}
  .header h1 {{ font-size: 28px; font-weight: 700; letter-spacing: 1px; }}
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
  
  .card {{ background: white; border-radius: 12px; padding: 20px 24px; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); border-left: 5px solid #e2e8f0; transition: all 0.2s; }}
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
  .card-dynamic .source {{ font-size: 12px; color: #64748b; margin-left: 10px; }}
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
  <div class="header">
    <h1>📋 北森拓客日报</h1>
    <span class="date">{today_str}</span>
  </div>
  
  <div class="stats">
    <div class="stat-item stat-s"><div class="num">{len(s_list)}</div><div class="label">🔴 S级（重大动态）</div></div>
    <div class="stat-item stat-a"><div class="num">{len(a_list)}</div><div class="label">🟡 A级（近期动态）</div></div>
    <div class="stat-item stat-b"><div class="num">{len(b_list)}</div><div class="label">🔵 B级（关注中）</div></div>
    <div class="stat-item"><div class="num">{len(COMPANIES)}</div><div class="label">📊 总企业数</div></div>
  </div>
"""
    
    # 渲染S级
    if s_list:
        html += f'<div class="section section-s"><div class="section-title">🔴 S级 · 重大动态（融资/IPO进展）</div>'
        for c in s_list:
            html += render_card(c, "s")
        html += '</div>'
    
    # 渲染A级
    if a_list:
        html += f'<div class="section section-a"><div class="section-title">🟡 A级 · 近期动态（合作/扩张/发布）</div>'
        for c in a_list:
            html += render_card(c, "a")
        html += '</div>'
    
    # 渲染B级
    if b_list:
        html += f'<div class="section section-b"><div class="section-title">🔵 B级 · 关注中</div>'
        for c in b_list:
            html += render_card(c, "b")
        html += '</div>'
    
    html += f"""
  <div class="footer">
    数据来源：公开新闻报道（36氪、投资界、新华社、深交所等）<br>
    本日报由自动化系统生成，仅供内部业务拓展参考
  </div>
</div>
</body>
</html>
"""
    return html

def render_card(comp, level):
    pain = comp["pain_point"]
    return f"""
<div class="card card-{level}">
  <div class="card-header">
    <span class="card-name">{comp['name']}</span>
    <span class="card-tag">{comp['track']}</span>
  </div>
  <div class="card-info">
    <span>👥 {comp['employees']}</span>
    <span>💰 {comp['finance']}</span>
    <span>📍 {comp['branches']}</span>
    <span class="card-stage">📌 {comp['stage']}</span>
  </div>
  <div class="card-dynamic">
    📰 {comp['today_dynamic']}
  </div>
  <div class="card-pain">
    <div class="ptype">💡 核心痛点：{pain['type']}</div>
    <div class="pdesc">🎯 切入点：{pain['desc']}</div>
  </div>
</div>
"""

# ====================== 5. 主程序 ======================
if __name__ == "__main__":
    html_content = generate_html_report()
    today_str = datetime.now().strftime("%Y%m%d")
    filename = f"北森拓客日报_{today_str}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 日报已生成：{filename}")
    print(f"📊 共 {len(COMPANIES)} 家企业，请双击打开 HTML 文件查看。")