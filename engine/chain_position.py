"""
产业链位置判断
判断企业所在产业链层级，并提供强弱缺失环节定义。
"""

from typing import Dict, List


# 细分领域 -> 产业链层级
SEGMENT_LAYER_MAP = {
    # 上游
    "正极材料": ("上游", "核心零部件材料"),
    "负极材料": ("上游", "核心零部件材料"),
    "电解液": ("上游", "核心零部件材料"),
    "锂盐/锂矿": ("上游", "原材料"),
    "动力电池隔膜": ("上游", "核心零部件材料"),
    "电机材料": ("上游", "原材料"),
    "生产设备": ("上游", "生产设备"),
    "检测设备": ("上游", "生产设备"),
    # 中游
    "动力电池电芯": ("中游", "核心制造"),
    "电池包集成": ("中游", "系统集成"),
    "BMS系统": ("中游", "关键平台"),
    "驱动电机": ("中游", "核心制造"),
    "电机控制器": ("中游", "关键平台"),
    "减速器": ("中游", "核心制造"),
    "车载芯片": ("中游", "关键平台"),
    "激光雷达": ("中游", "关键平台"),
    "车载操作系统": ("中游", "关键平台"),
    "高精地图": ("中游", "关键平台"),
    "高精度传感器": ("中游", "关键平台"),
    # 下游
    "乘用车制造": ("下游", "终端应用"),
    "商用车制造": ("下游", "终端应用"),
    "充电桩": ("下游", "运营服务"),
    "换电站": ("下游", "运营服务"),
    "运营平台": ("下游", "运营服务"),
    "售后服务": ("下游", "后市场"),
    "金融服务": ("下游", "后市场"),
    "二手车/回收": ("下游", "后市场"),
    "其他配套": ("上游", "服务支撑"),
}

# 参考环节（用于完整度计算）
REFERENCE_SEGMENTS = list(SEGMENT_LAYER_MAP.keys())

# 强弱缺失环节定义
STRONG_SEGMENTS = ["正极材料", "负极材料", "动力电池电芯", "电池包集成", "整车制造", "充换电设施"]
WEAK_SEGMENTS = ["电解液", "车载芯片", "激光雷达", "电机控制器"]
MISSING_SEGMENTS = ["锂盐/锂矿", "动力电池隔膜", "高精度传感器"]

# 风险环节（技术门槛高且缺失/薄弱）
RISK_SEGMENTS = ["锂盐/锂矿", "动力电池隔膜", "高精度传感器", "车载芯片", "激光雷达"]


def position(segment: str) -> Dict[str, str]:
    """
    根据细分领域判断产业链位置。

    返回：
        {"layer": "上游/中游/下游", "detail": "..."}
    """
    layer, detail = SEGMENT_LAYER_MAP.get(segment, ("中游", "其他"))
    return {"layer": layer, "detail": detail}


def classify_segment_strength(segment: str, enterprise_count: int = 0, total_revenue: float = 0.0) -> str:
    """
    根据企业数量和产值判断环节强弱状态。
    """
    if segment in MISSING_SEGMENTS:
        return "缺失"
    if segment in WEAK_SEGMENTS:
        return "薄弱"
    if segment in STRONG_SEGMENTS:
        return "强势"
    if enterprise_count == 0:
        return "缺失"
    if enterprise_count <= 1:
        return "薄弱"
    if enterprise_count >= 3 or total_revenue >= 10:
        return "强势"
    return "正常"


def get_reference_segments() -> List[str]:
    """返回参考产业链环节列表"""
    return REFERENCE_SEGMENTS.copy()


def get_strong_segments() -> List[str]:
    return STRONG_SEGMENTS.copy()


def get_weak_segments() -> List[str]:
    return WEAK_SEGMENTS.copy()


def get_missing_segments() -> List[str]:
    return MISSING_SEGMENTS.copy()


def get_risk_segments() -> List[str]:
    return RISK_SEGMENTS.copy()
