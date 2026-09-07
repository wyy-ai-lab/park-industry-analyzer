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
    }
