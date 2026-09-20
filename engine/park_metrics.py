"""
园区指标计算
提供园区产业分析所需的各项核心指标计算。
"""

import json
import os
from collections import Counter
from typing import Dict, List, Any, Optional

from .chain_position import (
    REFERENCE_SEGMENTS,
    STRONG_SEGMENTS,
    WEAK_SEGMENTS,
    MISSING_SEGMENTS,
    RISK_SEGMENTS,
)


def load_park_enterprises(file_path: str = "data/park_enterprises.json") -> Dict[str, Any]:
    """加载园区企业数据

    支持「演示数据开关」：当用户在界面关闭演示数据时，
    返回空数据以模拟“尚未接入园区数据”的状态。
    """
    try:
        import streamlit as st
        if st.session_state.get("use_demo_data", True) is False:
            return {}
    except Exception:
        pass

    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_enterprises(data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """获取企业列表"""
    if data is None:
        data = load_park_enterprises()
    return data.get("enterprises", [])


def compute_totals(enterprises: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算总量指标"""
    total_revenue = sum(e.get("annual_revenue", 0) for e in enterprises)
    total_employees = sum(e.get("employees", 0) for e in enterprises)
    high_tech_count = sum(1 for e in enterprises if e.get("high_tech_enterprise"))
    little_giant_count = sum(1 for e in enterprises if e.get("little_giant"))

    return {
        "enterprise_count": len(enterprises),
        "total_revenue": round(total_revenue, 2),
        "total_employees": total_employees,
        "high_tech_count": high_tech_count,
        "little_giant_count": little_giant_count,
    }


def compute_chain_distribution(enterprises: List[Dict[str, Any]]) -> Dict[str, int]:
    """计算产业链层级分布"""
    counts = Counter(e.get("chain_position", "未知") for e in enterprises)
    return {
        "上游": counts.get("上游", 0),
        "中游": counts.get("中游", 0),
        "下游": counts.get("下游", 0),
    }


def compute_tier_distribution(enterprises: List[Dict[str, Any]]) -> Dict[str, int]:
    """计算企业梯队分布"""
    counts = Counter(e.get("enterprise_role", "未知") for e in enterprises)
    return {
        "链主企业": counts.get("链主企业", 0),
        "骨干企业": counts.get("骨干企业", 0),
        "高新技术企业": counts.get("高新技术企业", 0),
        "科技型中小企业": counts.get("科技型中小企业", 0),
        "配套服务企业": counts.get("配套服务企业", 0),
    }


def compute_sub_industry_distribution(enterprises: List[Dict[str, Any]]) -> Dict[str, int]:
    """计算产业领域分布"""
    return dict(Counter(e.get("sub_industry", "未知") for e in enterprises))


def compute_segment_distribution(enterprises: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """计算产业链细分领域分布，包含企业数、产值、代表企业"""
    segments = {}
    for e in enterprises:
        niche = e.get("niche", "未知")
        if niche not in segments:
            segments[niche] = {
                "count": 0,
                "revenue": 0.0,
                "enterprises": [],
                "chain_position": e.get("chain_position", "未知"),
            }
        segments[niche]["count"] += 1
        segments[niche]["revenue"] += e.get("annual_revenue", 0)
        segments[niche]["enterprises"].append(e.get("name", ""))

    for niche in segments:
        segments[niche]["revenue"] = round(segments[niche]["revenue"], 2)

    return segments


def local_support_rate(enterprises: List[Dict[str, Any]]) -> float:
    """
    本地配套率估算：有本地供应商的企业占比。
    """
    if not enterprises:
        return 0.0
    with_local = sum(1 for e in enterprises if e.get("local_suppliers"))
    return round(with_local / len(enterprises) * 100, 1)


def completeness_score(enterprises: List[Dict[str, Any]]) -> float:
    """
    产业链完整度评分：已布局环节 / 参考总环节。
    """
    if not enterprises:
        return 0.0
    covered = set(e.get("niche") for e in enterprises if e.get("niche"))
    total = len(REFERENCE_SEGMENTS)
    return round(len(covered) / total * 100, 1)


def segment_strength_analysis(enterprises: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    分析产业链环节强弱缺失。
    """
    segment_dist = compute_segment_distribution(enterprises)
    covered = set(segment_dist.keys())

    strong = [s for s in STRONG_SEGMENTS if s in covered and segment_dist[s]["count"] > 0]
    weak = [s for s in WEAK_SEGMENTS if s in covered and segment_dist[s]["count"] > 0]
    missing = [s for s in MISSING_SEGMENTS if s not in covered]
    risk = [s for s in RISK_SEGMENTS if s in missing or (s in covered and s in WEAK_SEGMENTS)]

    return {
        "strong": strong,
        "weak": weak,
        "missing": missing,
        "risk": risk,
    }


def compute_innovation_metrics(enterprises: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算创新密度指标"""
    total_patents = sum(e.get("patents", 0) for e in enterprises)
    total_invention = sum(e.get("invention_patents", 0) for e in enterprises)
    total_rd_personnel = sum(e.get("rd_personnel", 0) for e in enterprises)
    avg_rd_ratio = (
        sum(e.get("rd_investment_ratio", 0) for e in enterprises) / len(enterprises)
        if enterprises else 0
    )

    return {
        "total_patents": total_patents,
        "total_invention_patents": total_invention,
        "total_rd_personnel": total_rd_personnel,
        "avg_rd_ratio": round(avg_rd_ratio * 100, 2),
        "patents_per_enterprise": round(total_patents / len(enterprises), 1) if enterprises else 0,
    }


def compute_top_enterprises(enterprises: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    """按年产值排序返回头部企业"""
    sorted_ents = sorted(enterprises, key=lambda x: x.get("annual_revenue", 0), reverse=True)
    return sorted_ents[:top_n]


def compute_cultivation_candidates(enterprises: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """识别重点培育候选企业（高企 / 小巨人 / 骨干升级），输出点名建议"""
    candidates = []

    # 高企培育候选：非高企、营收与研发达到一定规模
    for e in enterprises:
        if e.get("high_tech_enterprise"):
            continue
        revenue = e.get("annual_revenue", 0)
        rd_ratio = e.get("rd_investment_ratio", 0)
        if revenue >= 3 and rd_ratio >= 0.03:
            gap_parts = []
            if e.get("invention_patents", 0) < 3:
                gap_parts.append(f"发明专利仅 {e.get('invention_patents', 0)} 项（建议 3 项以上）")
            if rd_ratio < 0.04:
                gap_parts.append(f"研发占比 {rd_ratio * 100:.1f}%（建议 4% 以上）")
            candidates.append({
                "name": e.get("name", ""),
                "category": "高企培育",
                "sub_industry": e.get("sub_industry", ""),
                "niche": e.get("niche", ""),
                "basis": f"年产值 {revenue:.1f} 亿元、研发占比 {rd_ratio * 100:.1f}%，已达高企申报体量",
                "suggestion": "；".join(gap_parts) if gap_parts else "基本达标，建议尽快组织申报",
            })

    # 小巨人培育候选：已是高企、非小巨人、发明专利较多
    for e in enterprises:
        if not e.get("high_tech_enterprise") or e.get("little_giant"):
            continue
        if e.get("invention_patents", 0) >= 5 and e.get("annual_revenue", 0) >= 2:
            candidates.append({
                "name": e.get("name", ""),
                "category": "小巨人培育",
                "sub_industry": e.get("sub_industry", ""),
                "niche": e.get("niche", ""),
                "basis": f"已是高企，发明专利 {e.get('invention_patents', 0)} 项、年产值 {e.get('annual_revenue', 0):.1f} 亿元",
                "suggestion": "建议对照专精特新“小巨人”指标补齐市场占有率证明与细分赛道专注度材料",
            })

    # 骨干升级候选：科技型中小企业中研发突出的
    for e in enterprises:
        if e.get("enterprise_role") != "科技型中小企业":
            continue
        if e.get("rd_investment_ratio", 0) >= 0.06 and e.get("patents", 0) >= 8:
            candidates.append({
                "name": e.get("name", ""),
                "category": "骨干升级",
                "sub_industry": e.get("sub_industry", ""),
                "niche": e.get("niche", ""),
                "basis": f"研发占比 {e.get('rd_investment_ratio', 0) * 100:.1f}%、专利 {e.get('patents', 0)} 项，成长性突出",
                "suggestion": "建议纳入骨干企业库，给予研发补助与场景开放支持，冲击高新技术企业",
            })

    # 每类最多保留 3 家，控制报告篇幅
    result = []
    for cat in ("高企培育", "小巨人培育", "骨干升级"):
        result.extend([c for c in candidates if c["category"] == cat][:3])
    return result


# 招商目标画像（Demo）：目标环节 -> 潜在配套对象（园区企业）所在环节
_INVEST_TARGET_PARTNER_HINTS = {
    "锂盐/锂矿": ["正极材料", "电解液"],
    "动力电池隔膜": ["动力电池电芯", "电池包集成"],
    "高精度传感器": ["车载芯片", "BMS系统", "激光雷达"],
    "车载芯片": ["乘用车制造", "商用车制造"],
    "激光雷达": ["乘用车制造", "商用车制造"],
    "电解液": ["动力电池电芯"],
    "电机控制器": ["驱动电机"],
}

# 招商目标画像（Demo）：目标环节 -> 虚构演示企业名称池
_INVEST_TARGET_NAME_POOLS = {
    "锂盐/锂矿": ["（演示）川能锂业科技", "（演示）中矿锂源材料"],
    "动力电池隔膜": ["（演示）蓝科隔膜科技", "（演示）晟阳膜材料"],
    "高精度传感器": ["（演示）精测传感科技", "（演示）微纳感知技术"],
    "车载芯片": ["（演示）芯驰半导体", "（演示）杰发智芯科技"],
    "激光雷达": ["（演示）禾光感知技术", "（演示）镭神光电科技"],
    "电解液": ["（演示）昆仑电解液科技", "（演示）蓝帆新能源材料"],
    "电机控制器": ["（演示）精控电驱科技", "（演示）威迈斯电控"],
}

# 招商目标画像（Demo）：候选所在地（长三角/中部供应链圈内城市）
_INVEST_TARGET_LOCATIONS = [
    "江苏常州", "江苏苏州", "江苏无锡", "浙江宁波",
    "安徽合肥", "湖北武汉", "湖南长沙", "上海嘉定",
]

# 招商目标画像（Demo）：落地信号话术池
_INVEST_TARGET_SIGNALS = [
    "近期发布扩产公告，规划新生产基地",
    "正在筹备新设华东区域子公司",
    "获得新一轮融资，规划新增产能",
    "与本地整车厂已有小规模供货试点",
]


def _segment_hash(segment: str) -> int:
    """稳定的环节散列值，用于确定性生成演示数据"""
    return sum(ord(ch) for ch in segment)


def _resolve_partners(segment: str, segment_dist: Dict[str, Dict[str, Any]]) -> str:
    """解析潜在配套对象：优先映射到园区已有环节的头部企业"""
    for hint in _INVEST_TARGET_PARTNER_HINTS.get(segment, []):
        if hint in segment_dist and segment_dist[hint]["enterprises"]:
            names = list(dict.fromkeys(segment_dist[hint]["enterprises"]))[:2]
            return "、".join(names)
    # 兜底：下游环节中的代表企业
    downstream = [seg for seg in ("乘用车制造", "商用车制造") if seg in segment_dist]
    for seg in downstream:
        if segment_dist[seg]["enterprises"]:
            names = list(dict.fromkeys(segment_dist[seg]["enterprises"]))[:2]
            return "、".join(names)
    return "园区链主企业（待匹配）"


def _build_targets_for_segment(
    segment: str, priority: str, segment_dist: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """为一个缺失/风险/薄弱环节生成 2 家演示目标企业画像（确定性）"""
    h = _segment_hash(segment)
    names = _INVEST_TARGET_NAME_POOLS.get(segment, [f"（演示）{segment}龙头企业A", f"（演示）{segment}成长企业B"])
    partners = _resolve_partners(segment, segment_dist)
    status_label = "缺失" if priority == "高" else "薄弱"
    targets = []
    for i, name in enumerate(names[:2]):
        revenue = round(3 + ((h + i * 7) % 12), 1)          # 3–14 亿元
        patents = 5 + ((h + i * 11) % 25)                    # 5–29 项
        location = _INVEST_TARGET_LOCATIONS[(h + i * 3) % len(_INVEST_TARGET_LOCATIONS)]
        signal = _INVEST_TARGET_SIGNALS[(h + i * 5) % len(_INVEST_TARGET_SIGNALS)]
        reason = (
            f"园区「{segment}」环节{status_label}，本地{partners.split('、')[0]}等企业急需配套；"
            f"该企业营收 {revenue} 亿元、发明专利 {patents} 项，符合实力门槛"
        )
        targets.append({
            "name": name,
            "location": location,
            "segment": segment,
            "revenue": f"{revenue} 亿元",
            "invention_patents": patents,
            "partners": partners,
            "signal": signal,
            "priority": priority,
            "reason": reason,
        })
    return targets


def compute_investment_targets(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    生成招商目标清单（Demo）：对缺失/风险环节生成高优先级目标，薄弱环节生成中优先级目标。

    当前为规则生成的演示目标画像（虚构企业名称）；
    接入工商/知产数据库后替换为真实检索结果。
    """
    segment_dist = metrics.get("segment_distribution", {})
    strength = metrics.get("segment_strength", {})
    seen = set()
    targets: List[Dict[str, Any]] = []
    # 缺失/风险环节（risk 为 missing 的子集，需去重）→ 高优先级
    for seg in strength.get("missing", []) + strength.get("risk", []):
        if seg in seen:
            continue
        seen.add(seg)
        targets.extend(_build_targets_for_segment(seg, "高", segment_dist))
    for seg in strength.get("weak", []):
        if seg in seen:
            continue
        seen.add(seg)
        targets.extend(_build_targets_for_segment(seg, "中", segment_dist))
    return targets


def compute_park_health_index(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    产业健康指数：将完整度、配套率、创新密度、梯队结构加权合成为 0–100 综合指数。
    权重：产业链完整度 30% · 本地配套率 25% · 创新密度 25% · 梯队结构 20%
    """
    completeness = float(metrics.get("completeness_score", 0))
    support_rate = float(metrics.get("local_support_rate", 0))

    innovation = metrics.get("innovation", {})
    avg_rd_ratio = float(innovation.get("avg_rd_ratio", 0))
    patents_per_ent = float(innovation.get("patents_per_enterprise", 0))
    innovation_score = min(100.0, round(avg_rd_ratio * 6 + patents_per_ent * 1.2, 1))

    tier_dist = metrics.get("tier_distribution", {})
    total = sum(tier_dist.values()) or 1
    # 链主 3 分 / 骨干 2 分 / 高企 1 分 / 科技型中小企业 0.5 分，归一化到 0–100
    tier_score = (
        tier_dist.get("链主企业", 0) * 3
        + tier_dist.get("骨干企业", 0) * 2
        + tier_dist.get("高新技术企业", 0)
        + tier_dist.get("科技型中小企业", 0) * 0.5
    )
    structure_score = min(100.0, round(tier_score * 100 / (3 * total), 1))

    dimensions = {
        "产业链完整度": round(completeness, 1),
        "本地配套率": round(support_rate, 1),
        "创新密度": innovation_score,
        "梯队结构": structure_score,
    }
    weights = {"产业链完整度": 0.30, "本地配套率": 0.25, "创新密度": 0.25, "梯队结构": 0.20}
    score = round(sum(dimensions[k] * weights[k] for k in dimensions), 1)
    grade = "优秀" if score >= 85 else "良好" if score >= 70 else "一般" if score >= 55 else "待提升"
    return {"score": score, "grade": grade, "dimensions": dimensions, "weights": weights}


def compute_metric_trends(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成近三年核心指标趋势（Demo：基于当前值按固定增速确定性回溯）。

    演示数据为单期快照，此处以规则回溯 2023–2025 序列以展示时间维度分析能力；
    接入真实数据后替换为历年台账统计。
    """
    this_year = 2025
    years = [this_year - 2, this_year - 1, this_year]

    revenue_now = float(metrics.get("totals", {}).get("total_revenue", 0))
    completeness_now = float(metrics.get("completeness_score", 0))
    support_now = float(metrics.get("local_support_rate", 0))

    revenue_growth = 0.12   # 产值年增速假设
    revenue = [round(revenue_now / (1 + revenue_growth) ** k, 1) for k in (2, 1, 0)]
    completeness = [round(max(0, completeness_now - 4 * k), 1) for k in (2, 1, 0)]
    support_rate = [round(max(0, support_now - 3 * k), 1) for k in (2, 1, 0)]

    return {
        "years": years,
        "revenue": revenue,
        "completeness": completeness,
        "support_rate": support_rate,
        "note": "演示数据为规则回溯生成的趋势序列，接入真实台账后替换为历年统计。",
    }


# 技术赛道标签体系：细分领域 -> 技术赛道（Demo 版）
TECH_TRACK_MAP = {
    "正极材料": "电池材料", "负极材料": "电池材料", "电解液": "电池材料",
    "锂盐/锂矿": "电池材料", "动力电池隔膜": "电池材料",
    "电机材料": "电驱动", "驱动电机": "电驱动", "电机控制器": "电驱动", "减速器": "电驱动",
    "车载芯片": "智能网联", "激光雷达": "智能网联", "车载操作系统": "智能网联",
    "高精地图": "智能网联", "高精度传感器": "智能网联", "BMS系统": "智能网联",
    "动力电池电芯": "整车集成", "电池包集成": "整车集成",
    "乘用车制造": "整车集成", "商用车制造": "整车集成",
    "充电桩": "能源补给", "换电站": "能源补给", "运营平台": "能源补给",
    "生产设备": "装备与后市场", "检测设备": "装备与后市场",
    "售后服务": "装备与后市场", "金融服务": "装备与后市场",
    "二手车/回收": "装备与后市场", "其他配套": "装备与后市场",
}

_LAYER_NUM = {"上游": 1, "中游": 2, "下游": 3}


def compute_tech_landscape(enterprises: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    技术图谱：按技术赛道聚合企业的数量、产值、专利与核心技术方向。
    """
    tracks: Dict[str, Dict[str, Any]] = {}
    for e in enterprises:
        niche = e.get("niche", "未知")
        track = TECH_TRACK_MAP.get(niche, "其他")
        t = tracks.setdefault(track, {
            "track": track,
            "count": 0,
            "revenue": 0.0,
            "invention_patents": 0,
            "layer_weight": 0,
            "layers": {"上游": 0, "中游": 0, "下游": 0},
            "core_techs": [],
            "top_enterprise": "",
            "top_revenue": -1.0,
        })
        t["count"] += 1
        t["revenue"] = round(t["revenue"] + e.get("annual_revenue", 0), 2)
        t["invention_patents"] += e.get("invention_patents", 0)
        layer = e.get("chain_position", "中游")
        t["layers"][layer] = t["layers"].get(layer, 0) + 1
        t["layer_weight"] += _LAYER_NUM.get(layer, 2)
        core = (e.get("core_technology") or "").strip()
        if core and core not in t["core_techs"]:
            t["core_techs"].append(core)
        if e.get("annual_revenue", 0) > t["top_revenue"]:
            t["top_revenue"] = e.get("annual_revenue", 0)
            t["top_enterprise"] = e.get("name", "")

    result = []
    for t in tracks.values():
        t["avg_layer"] = round(t["layer_weight"] / t["count"], 2) if t["count"] else 0
        t["core_techs"] = t["core_techs"][:3]
        result.append(t)
    return sorted(result, key=lambda x: x["invention_patents"], reverse=True)


def compute_metrics(data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    计算园区产业分析全部核心指标。
    """
    if data is None:
        data = load_park_enterprises()

    enterprises = get_enterprises(data)

    return {
        "park_name": data.get("park_name", "未知园区"),
        "total_enterprises": data.get("total_enterprises", len(enterprises)),
        "totals": compute_totals(enterprises),
        "chain_distribution": compute_chain_distribution(enterprises),
        "tier_distribution": compute_tier_distribution(enterprises),
        "sub_industry_distribution": compute_sub_industry_distribution(enterprises),
        "segment_distribution": compute_segment_distribution(enterprises),
        "local_support_rate": local_support_rate(enterprises),
        "completeness_score": completeness_score(enterprises),
        "segment_strength": segment_strength_analysis(enterprises),
        "innovation": compute_innovation_metrics(enterprises),
        "top_enterprises": compute_top_enterprises(enterprises, top_n=10),
        "cultivation_candidates": compute_cultivation_candidates(enterprises),
        "investment_targets": compute_investment_targets(
            {
                "segment_distribution": compute_segment_distribution(enterprises),
                "segment_strength": segment_strength_analysis(enterprises),
            }
        ),
        "health_index": compute_park_health_index(
            {
                "completeness_score": completeness_score(enterprises),
                "local_support_rate": local_support_rate(enterprises),
                "innovation": compute_innovation_metrics(enterprises),
                "tier_distribution": compute_tier_distribution(enterprises),
            }
        ),
        "metric_trends": compute_metric_trends(
            {
                "totals": compute_totals(enterprises),
                "completeness_score": completeness_score(enterprises),
                "local_support_rate": local_support_rate(enterprises),
            }
        ),
        "tech_landscape": compute_tech_landscape(enterprises),
    }
