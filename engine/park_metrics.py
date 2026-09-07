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
    }
