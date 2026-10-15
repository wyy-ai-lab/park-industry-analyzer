"""
问题型园区演示数据生成器
=========================
生成「问题型园区」演示数据集（data/park_enterprises_problem.json），
与健康型园区（data/park_enterprises.json）组成双故事线演示：

- 健康型园区：完整度高、配套率高，讲"成绩汇报"场景
- 问题型园区：链条残缺、配套断裂、梯队单薄，讲"诊断 + 招商补链"场景

设计的故事（芜湖江北新能源汽车零部件产业园 · 演示）：
- 下游过重、上游空心：整车/充换电扎堆，核心材料与动力电池环节全部缺失
- 单点依赖：一家链主整车厂贡献近 40% 产值，抗风险能力弱
- 配套断裂：本地配套率约 25%，多数企业供应链在园区外
- 创新不足：高企占比低、无小巨人，平均研发占比约 2.5%

生成是确定性的（环节散列 + 序号驱动），重复运行产出完全一致。
调整故事强度时，改下方 CONFIG 即可（如 LOCAL_SUPPLIER_RATIO）。
"""

import json
from datetime import datetime

PARK = {
    "park_name": "芜湖江北新能源汽车零部件产业园",
    "total_enterprises": 24,
    "strong_segments": ["乘用车制造", "商用车制造", "充电桩", "售后服务"],
    "weak_segments": ["电池包集成", "电机控制器", "BMS系统", "驱动电机"],
    "missing_segments": [
        "锂盐/锂矿", "正极材料", "负极材料", "电解液", "动力电池隔膜",
        "动力电池电芯", "电机材料", "车载芯片", "激光雷达",
        "车载操作系统", "高精地图", "高精度传感器",
    ],
}

CONFIG = {
    "local_supplier_ratio": 0.25,   # 有本地供应商的企业占比（健康园区约 68%）
    "high_tech_ratio": 0.17,        # 高企占比（健康园区 40%）
    "chain_leader_revenue": 45.0,   # 链主产值（亿元），园区总产值约 1/3 靠它
    "avg_rd_ratio": 0.025,          # 平均研发占比（健康园区约 5%+）
}

# 环节布局：(niche, 企业数, 角色池, 备注)
# 下游扎堆 + 中游薄弱 + 上游仅剩装备，核心材料/电芯/智能化全部缺席
LAYOUT = [
    ("乘用车制造", 3, ["链主企业", "骨干企业", "高新技术企业"]),
    ("商用车制造", 2, ["骨干企业", "配套服务企业"]),
    ("充电桩", 3, ["高新技术企业", "科技型中小企业", "配套服务企业"]),
    ("换电站", 1, ["科技型中小企业"]),
    ("运营平台", 1, ["科技型中小企业"]),
    ("售后服务", 2, ["配套服务企业", "配套服务企业"]),
    ("金融服务", 1, ["配套服务企业"]),
    ("二手车/回收", 1, ["配套服务企业"]),
    ("驱动电机", 2, ["高新技术企业", "科技型中小企业"]),
    ("电机控制器", 1, ["高新技术企业"]),
    ("减速器", 1, ["科技型中小企业"]),
    ("BMS系统", 1, ["科技型中小企业"]),
    ("电池包集成", 1, ["高新技术企业"]),
    ("生产设备", 1, ["配套服务企业"]),
    ("检测设备", 1, ["科技型中小企业"]),
    ("其他配套", 2, ["配套服务企业", "配套服务企业"]),
]

SUB_INDUSTRY = {
    "乘用车制造": "整车制造", "商用车制造": "整车制造",
    "充电桩": "充换电设施", "换电站": "充换电设施", "运营平台": "充换电设施",
    "驱动电机": "电驱动系统", "电机控制器": "电驱动系统", "减速器": "电驱动系统",
    "电池包集成": "动力电池", "BMS系统": "动力电池",
    "售后服务": "汽车服务", "金融服务": "汽车服务", "二手车/回收": "汽车服务",
    "生产设备": "装备制造", "检测设备": "装备制造",
    "其他配套": "其他配套",
}

LAYER = {"生产设备": ("上游", "生产设备"), "检测设备": ("上游", "生产设备"),
         "其他配套": ("上游", "服务支撑")}
for _seg in ("乘用车制造", "商用车制造"):
    LAYER[_seg] = ("下游", "终端应用")
for _seg in ("充电桩", "换电站", "运营平台"):
    LAYER[_seg] = ("下游", "运营服务")
for _seg in ("售后服务", "金融服务", "二手车/回收"):
    LAYER[_seg] = ("下游", "后市场")
for _seg in ("驱动电机", "电机控制器", "减速器", "电池包集成", "BMS系统"):
    LAYER[_seg] = ("中游", "核心制造")

PRODUCTS = {
    "乘用车制造": "纯电动乘用车", "商用车制造": "电动物流车",
    "充电桩": "直流快充桩", "换电站": "乘用车换电站", "运营平台": "车桩一体化运营平台",
    "驱动电机": "永磁同步驱动电机", "电机控制器": "电机控制器总成",
    "减速器": "电驱动减速器", "BMS系统": "动力电池管理系统",
    "电池包集成": "动力电池Pack集成",
    "售后服务": "新能源车维保服务", "金融服务": "汽车融资租赁",
    "二手车/回收": "动力电池回收梯次利用",
    "生产设备": "焊装线配套设备", "检测设备": "整车下线检测设备",
    "其他配套": "物流与仓储配套",
}

TECHS = {
    "乘用车制造": "整车轻量化集成", "商用车制造": "商用车电动化平台",
    "充电桩": "大功率快充模块", "换电站": "全自动换电机构", "运营平台": "充电调度算法",
    "驱动电机": "高功率密度电机设计", "电机控制器": "IGBT功率模块应用",
    "减速器": "高精度齿轮加工", "BMS系统": "电池状态估算算法",
    "电池包集成": "Pack结构设计与热管理",
    "售后服务": "高压系统检修工艺", "金融服务": "电池银行租赁模式",
    "二手车/回收": "电池残值评估", "生产设备": "产线自动化集成",
    "检测设备": "EOL下线检测", "其他配套": "供应链协同",
}

CHAIN_LEADER = "江北智造汽车有限公司"
LEADER_SUPPLIERS = ["（园区外）苏州汇川电驱", "（园区外）宁波容百正极材料"]
LEADER_CUSTOMERS = ["（市外）省网约车采购平台", "（市外）长三角公交集团"]

OUTSIDE_SUPPLIERS = [
    "（园区外）常州中创新航电芯", "（园区外）江西赣锋锂业",
    "（园区外）苏州绿的谐波", "（园区外）深圳德赛西威",
    "（园区外）上海电驱动", "（园区外）合肥国轩材料",
]
OUTSIDE_CUSTOMERS = [
    "（市外）省新能源物流车队", "（市外）周边城市公交公司",
    "（市外）长三角网约车平台", "（市外）省内政务采购平台",
]
LOCAL_PARTNERS = [
    "江北智造汽车有限公司", "芜湖绿能充电桩有限公司",
    "江城电驱动科技有限公司", "江北安捷售后服务有限公司",
]


def _hash(s: str) -> int:
    return sum(ord(c) for c in s)


def _local_roster(names, n, seed):
    return [names[(seed + i * 3) % len(names)] for i in range(n)]


def build_enterprise(seq: int, niche: str, role: str) -> dict:
    h = _hash(niche) + seq * 17
    layer, detail = LAYER[niche]

    if role == "链主企业":
        name = CHAIN_LEADER
        revenue = CONFIG["chain_leader_revenue"]
        employees = 5200
        founded = 2016
        rd_ratio = 0.035
        patents, invention = 88, 31
        high_tech, giant = True, False
        suppliers = LEADER_SUPPLIERS
        customers = LEADER_CUSTOMERS
        local_sup = ["江城电驱动科技有限公司", "江北安捷售后服务有限公司"]
    else:
        suffix = {"骨干企业": "股份有限公司", "高新技术企业": "有限公司",
                  "科技型中小企业": "科技有限公司", "配套服务企业": "有限公司"}[role]
        name = f"（演示）{CORE_NAME[niche]}{suffix}"
        base = {"骨干企业": 12, "高新技术企业": 6, "科技型中小企业": 2.2,
                "配套服务企业": 1.2}[role]
        revenue = round(base + (h % 7) * base * 0.12, 2)
        employees = int(revenue * 95 + (h % 40) * 12)
        founded = 2013 + (h % 10)
        rd_ratio = round(CONFIG["avg_rd_ratio"] + (h % 5) * 0.004, 3)
        patents = {"骨干企业": 25, "高新技术企业": 14,
                   "科技型中小企业": 4, "配套服务企业": 1}[role] + h % 6
        invention = max(0, int(patents * (0.25 if role in ("骨干企业", "高新技术企业") else 0.1)))
        high_tech = role in ("骨干企业", "高新技术企业")
        giant = False
        # 配套断裂：多数企业上下游在园区外
        if h % 4 == 0:
            suppliers = [_local_roster(LOCAL_PARTNERS, 1, h)[0]]
        else:
            suppliers = [OUTSIDE_SUPPLIERS[h % len(OUTSIDE_SUPPLIERS)]]
        customers = [OUTSIDE_CUSTOMERS[(h + 1) % len(OUTSIDE_CUSTOMERS)]]

    local_sup = local_sup if role == "链主企业" else (
        suppliers if (h % 4 == 0) else []
    )

    return {
        "enterprise_id": f"ENT{seq:03d}",
        "name": name,
        "founded_year": founded,
        "registered_capital": int(8000 + (h % 50) * 1200),
        "employees": employees,
        "annual_revenue": revenue,
        "net_profit": round(revenue * (0.04 + (h % 5) * 0.008), 2),
        "industry": "新能源汽车",
        "sub_industry": SUB_INDUSTRY[niche],
        "niche": niche,
        "chain_position": layer,
        "chain_position_detail": detail,
        "enterprise_role": role,
        "core_technology": TECHS[niche],
        "rd_investment_ratio": rd_ratio,
        "patents": patents,
        "invention_patents": invention,
        "software_copyrights": 1 + h % 6,
        "high_tech_enterprise": high_tech,
        "little_giant": giant,
        "main_products": PRODUCTS[niche],
        "upstream_suppliers": suppliers,
        "downstream_customers": customers,
        "local_suppliers": local_sup,
        "local_customers": local_sup if role == "链主企业" else (
            [CHAIN_LEADER] if niche in ("驱动电机", "电机控制器", "减速器",
                                        "BMS系统", "电池包集成", "售后服务") and h % 3 else []
        ),
        "rd_personnel": int(employees * rd_ratio * 0.9),
        "master_doctor_ratio": round(0.03 + (h % 4) * 0.01, 3),
        "leading_talents": h % 3,
        "university_cooperation": niche in ("驱动电机", "BMS系统", "乘用车制造"),
    }


CORE_NAME = {
    "乘用车制造": "整车", "商用车制造": "商用", "充电桩": "绿能充电",
    "换电站": "迅捷换电", "运营平台": "车联智行", "售后服务": "安捷售后",
    "金融服务": "产融", "二手车/回收": "循环再生", "驱动电机": "江城电驱动",
    "电机控制器": "精控电驱", "减速器": "恒力传动", "BMS系统": "智芯电池管理",
    "电池包集成": "聚能电池系统", "生产设备": "鼎力装备", "检测设备": "精测仪器",
    "其他配套": "迅达物流",
}


def main() -> None:
    enterprises = []
    seq = 1
    for niche, count, roles in LAYOUT:
        for i in range(count):
            enterprises.append(build_enterprise(seq, niche, roles[i % len(roles)]))
            seq += 1

    data = dict(PARK)
    data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["enterprises"] = enterprises

    out = "data/park_enterprises_problem.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total_rev = sum(e["annual_revenue"] for e in enterprises)
    with_local = sum(1 for e in enterprises if e["local_suppliers"])
    print(f"✅ 已生成 {out}")
    print(f"   企业数 {len(enterprises)}，总产值 {total_rev:.1f} 亿，"
          f"本地配套率 {with_local / len(enterprises) * 100:.0f}%，"
          f"高企 {sum(1 for e in enterprises if e['high_tech_enterprise'])} 家")


if __name__ == "__main__":
    main()
