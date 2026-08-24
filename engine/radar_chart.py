"""
企业能力雷达图模块
"""

from typing import Dict, Any, List
import plotly.graph_objects as go


# 能力维度定义：每个维度对应若干企业字段和打分规则
DIMENSION_RULES = {
    "经营规模": [
        {"field": "revenue", "weight": 0.5, "thresholds": [(0, 1000, 30), (1000, 3000, 50), (3000, 5000, 70), (5000, 10000, 85), (10000, float('inf'), 100)]},
        {"field": "employees", "weight": 0.3, "thresholds": [(0, 50, 40), (50, 100, 60), (100, 300, 80), (300, float('inf'), 100)]},
        {"field": "profit", "weight": 0.2, "thresholds": [(0, 0, 20), (0, 200, 50), (200, 500, 75), (500, float('inf'), 100)]},
    ],
    "研发投入": [
        {"field": "rd_ratio", "weight": 0.35, "thresholds": [(0, 0.03, 40), (0.03, 0.05, 65), (0.05, 0.08, 85), (0.08, float('inf'), 100)]},
        {"field": "rd_investment", "weight": 0.25, "thresholds": [(0, 100, 30), (100, 300, 55), (300, 500, 75), (500, float('inf'), 100)]},
        {"field": "rd_team_ratio", "weight": 0.25, "thresholds": [(0, 0.1, 40), (0.1, 0.2, 65), (0.2, 0.3, 85), (0.3, float('inf'), 100)]},
        {"field": "rd_accounting_system", "weight": 0.15, "boolean": True, "true_score": 100, "false_score": 30},
    ],
    "知识产权": [
        {"field": "invention_patents", "weight": 0.5, "thresholds": [(0, 0, 20), (0, 1, 50), (1, 3, 75), (3, float('inf'), 100)]},
        {"field": "utility_models", "weight": 0.2, "thresholds": [(0, 0, 30), (0, 2, 60), (2, 5, 80), (5, float('inf'), 100)]},
        {"field": "software_copyrights", "weight": 0.2, "thresholds": [(0, 0, 30), (0, 3, 60), (3, 10, 80), (10, float('inf'), 100)]},
        {"field": "trademarks", "weight": 0.1, "thresholds": [(0, 0, 30), (0, 1, 60), (1, 3, 80), (3, float('inf'), 100)]},
    ],
    "资质荣誉": [
        {"field": "qualifications", "weight": 0.6, "list": True, "high_value": ["国家高新技术企业", "国家级专精特新小巨人"], "mid_value": ["安徽省专精特新中小企业", "科技型中小企业", "创新型中小企业"], "low_value": ["ISO9001", "ISO13485", "CE认证"]},
        {"field": "is_high_tech_enterprise", "weight": 0.25, "boolean": True, "true_score": 100, "false_score": 20},
        {"field": "is_high_tech_field", "weight": 0.15, "boolean": True, "true_score": 100, "false_score": 40},
    ],
    "高新技术产业化": [
        {"field": "high_tech_income_ratio", "weight": 0.6, "thresholds": [(0, 0.5, 40), (0.5, 0.6, 65), (0.6, 0.7, 85), (0.7, float('inf'), 100)]},
        {"field": "market_share_proof", "weight": 0.4, "boolean": True, "true_score": 100, "false_score": 30},
    ],
    "合规与成长": [
        {"field": "has_major_accident", "weight": 0.4, "boolean": True, "true_score": 0, "false_score": 100, "inverse": True},
        {"field": "years_in_operation", "weight": 0.35, "thresholds": [(0, 1, 30), (1, 3, 60), (3, 10, 85), (10, float('inf'), 100)]},
        {"field": "rd_team_size", "weight": 0.25, "thresholds": [(0, 5, 30), (5, 15, 60), (15, 30, 80), (30, float('inf'), 100)]},
    ],
}


def _score_by_thresholds(value: float, thresholds: List[tuple]) -> int:
    """根据区间阈值打分"""
    for low, high, score in thresholds:
        if low <= value < high:
            return score
    return 0


def _score_field(rule: Dict[str, Any], enterprise: Dict[str, Any]) -> int:
    """根据规则为单个字段打分"""
    field = rule["field"]
    value = enterprise.get(field)

    if value is None:
        return 50  # 缺失数据按 50 分（待补充）处理

    if rule.get("boolean"):
        # 布尔字段
        true_score = rule.get("true_score", 100)
        false_score = rule.get("false_score", 0)
        return true_score if value else false_score

    if rule.get("list"):
        # 列表字段（资质）
        items = value if isinstance(value, list) else []
        high = rule.get("high_value", [])
        mid = rule.get("mid_value", [])
        low = rule.get("low_value", [])

        score = 0
        for item in items:
            if item in high:
                score = max(score, 100)
            elif item in mid:
                score = max(score, 80)
            elif item in low:
                score = max(score, 60)
        return score if score > 0 else 20

    # 数值字段
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 50

    return _score_by_thresholds(numeric_value, rule["thresholds"])


def calculate_dimension_scores(enterprise: Dict[str, Any]) -> Dict[str, int]:
    """
    根据企业画像计算各能力维度分数（0-100）

    返回：
        {"经营规模": 75, "研发投入": 60, ...}
    """
    scores = {}
    for dimension, rules in DIMENSION_RULES.items():
        total_score = 0
        total_weight = 0
        for rule in rules:
            field_score = _score_field(rule, enterprise)
            weight = rule.get("weight", 1.0)
            total_score += field_score * weight
            total_weight += weight
        scores[dimension] = int(round(total_score / total_weight)) if total_weight > 0 else 0
    return scores


def build_radar_chart(scores: Dict[str, int], title: str = "企业综合能力雷达图") -> go.Figure:
    """
    根据维度分数构建雷达图
    """
    categories = list(scores.keys())
    values = list(scores.values())

    # 闭合图形
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    fig = go.Figure(
        data=go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            name='当前企业',
            line_color='#1f77b4',
            fillcolor='rgba(31, 119, 180, 0.3)'
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10),
            ),
            angularaxis=dict(
                tickfont=dict(size=12),
            ),
        ),
        title=dict(
            text=title,
            font=dict(size=16)
        ),
        showlegend=False,
        margin=dict(l=60, r=60, t=60, b=40),
        height=450,
    )
    return fig


def fig_to_image_bytes(fig, format: str = 'png') -> bytes:
    """
    将 Plotly 图表转为图片 bytes

    依赖 kaleido。若未安装会抛出 ImportError，调用方需自行处理 fallback。
    """
    import plotly.io as pio
    return pio.to_image(fig, format=format, engine="kaleido")


def get_dimension_assessment(scores: Dict[str, int]) -> List[str]:
    """
    根据维度分数返回短板分析文本
    """
    suggestions = []
    if scores.get("研发投入", 0) < 60:
        suggestions.append("研发投入不足，建议完善研发费用辅助账并提高研发投入占比")
    if scores.get("知识产权", 0) < 60:
        suggestions.append("知识产权较弱，建议申请发明专利、软件著作权等核心知识产权")
    if scores.get("资质荣誉", 0) < 60:
        suggestions.append("资质荣誉较少，建议申报高新技术企业、专精特新等资质")
    if scores.get("高新技术产业化", 0) < 60:
        suggestions.append("高新技术产品收入占比或市场证明不足，需补充相关证明材料")
    if scores.get("经营规模", 0) < 60:
        suggestions.append("经营规模偏小，可关注对小微企业友好的专项政策")
    if scores.get("合规与成长", 0) < 60:
        suggestions.append("合规或成长数据存在短板，需排除安全质量事故并积累经营年限")
    return suggestions
