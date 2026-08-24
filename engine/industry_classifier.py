"""
产业分类器
根据企业名称、主营业务和产品识别产业标签。
"""

from typing import Dict, List


# 关键词映射到产业标签
INDUSTRY_KEYWORDS = {
    "新能源汽车": ["新能源汽车", "新能源", "电动汽车", "电动车", "电动化", "汽车"],
    "动力电池": ["动力电池", "锂电池", "锂离子电池", "磷酸铁锂", "三元锂", "固态电池", "电芯", "电池包", "BMS", "电池管理"],
    "电机电控": ["电机", "电控", "电驱动", "驱动电机", "控制器", "逆变器", "减速器", "动力总成"],
    "智能网联": ["智能网联", "智能驾驶", "自动驾驶", "车载芯片", "半导体", "激光雷达", "雷达", "车载系统", "操作系统", "高精地图", "车联网", "传感器"],
    "整车制造": ["整车", "乘用车", "商用车", "汽车制造", "汽车生产", "总装"],
    "充换电设施": ["充电桩", "充电站", "换电站", "换电", "充电运营", "充电平台"],
    "汽车服务": ["汽车服务", "售后服务", "汽车金融", "融资租赁", "二手车", "汽车回收", "再生资源", "梯次利用"],
    "其他配套": ["生产设备", "检测设备", "涂布机", "卷绕机", "产业园", "供应链", "物流", "孵化"],
}

# 关键词映射到细分领域
NICHE_KEYWORDS = {
    "正极材料": ["正极材料", "正极"],
    "负极材料": ["负极材料", "负极", "石墨", "碳材料"],
    "电解液": ["电解液", "电解质"],
    "动力电池电芯": ["电芯", "锂电池", "锂离子电池", "固态电池"],
    "电池包集成": ["电池包", "电池系统", "电池集成"],
    "BMS系统": ["BMS", "电池管理"],
    "驱动电机": ["驱动电机", "电机"],
    "电机控制器": ["电机控制器", "电控", "逆变器"],
    "减速器": ["减速器", "变速器", "传动"],
    "车载芯片": ["车载芯片", "车规级芯片", "半导体", "MCU"],
    "激光雷达": ["激光雷达", "雷达", "感知"],
    "车载操作系统": ["车载操作系统", "车机", "智能座舱", "T-BOX"],
    "高精地图": ["高精地图", "导航", "定位"],
    "乘用车制造": ["乘用车", "轿车", "SUV"],
    "商用车制造": ["商用车", "客车", "货车", "重卡", "轻卡"],
    "充电桩": ["充电桩", "充电站"],
    "换电站": ["换电站", "换电"],
    "运营平台": ["运营平台", "充电运营", "能源平台"],
    "售后服务": ["售后服务", "维保", "维修"],
    "金融服务": ["金融服务", "融资租赁", "汽车金融"],
    "二手车/回收": ["二手车", "回收", "梯次利用", "再生资源"],
    "生产设备": ["生产设备", "涂布机", "卷绕机", "装配线"],
    "检测设备": ["检测设备", "测试设备", "检测"],
    "其他配套": ["配套", "服务", "物流", "孵化", "产业园"],
}


def _contains_any(text: str, keywords: List[str]) -> bool:
    """检查文本中是否包含任一关键词（不区分大小写）"""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def classify(name: str = "", business: str = "", products: str = "") -> Dict:
    """
    根据企业名称、主营业务和产品识别产业标签与细分领域。

    返回：
        {
            "industry_tags": [...],      # 产业标签列表
            "niche_tags": [...],         # 细分领域标签列表
            "primary_industry": "...",   # 主要产业
            "primary_niche": "...",      # 主要细分领域
        }
    """
    combined = f"{name} {business} {products}"

    industry_tags = []
    for tag, keywords in INDUSTRY_KEYWORDS.items():
        if _contains_any(combined, keywords):
            industry_tags.append(tag)

    niche_tags = []
    for tag, keywords in NICHE_KEYWORDS.items():
        if _contains_any(combined, keywords):
            niche_tags.append(tag)

    # 去重并保持顺序
    industry_tags = list(dict.fromkeys(industry_tags))
    niche_tags = list(dict.fromkeys(niche_tags))

    primary_industry = industry_tags[0] if industry_tags else "其他"
    primary_niche = niche_tags[0] if niche_tags else "其他"

    return {
        "industry_tags": industry_tags,
        "niche_tags": niche_tags,
        "primary_industry": primary_industry,
        "primary_niche": primary_niche,
    }
