"""
园区可视化图表
提供园区产业分析所需的 Plotly 图表组件。
"""

from typing import Dict, List, Any

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Apple 风格配色
APPLE_BLUE = "#0071e3"
APPLE_GREEN = "#34c759"
APPLE_ORANGE = "#ff9500"
APPLE_RED = "#ff3b30"
APPLE_GRAY = "#8e8e93"
APPLE_PURPLE = "#af52de"
APPLE_TEAL = "#5ac8fa"

SEGMENT_STATUS_COLORS = {
    "强势": APPLE_BLUE,
    "正常": APPLE_GREEN,
    "薄弱": APPLE_ORANGE,
    "缺失": APPLE_RED,
    "服务支撑": APPLE_GRAY,
}

SUB_INDUSTRY_COLORS = {
    "动力电池": APPLE_BLUE,
    "电机电控": APPLE_GREEN,
    "智能网联": APPLE_PURPLE,
    "整车制造": APPLE_RED,
    "充换电设施": APPLE_ORANGE,
    "汽车服务": APPLE_TEAL,
    "其他配套": APPLE_GRAY,
}


def _apple_layout(fig: go.Figure, title: str, height: int = 420) -> go.Figure:
    """统一应用 Apple 风格布局"""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#1d1d1f")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, sans-serif",
            color="#1d1d1f",
        ),
        margin=dict(l=24, r=24, t=60, b=32),
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.5)",
        ),
    )
    return fig


def build_industry_pie_chart(sub_industry_dist: Dict[str, int]) -> go.Figure:
    """产业分布饼图"""
    labels = list(sub_industry_dist.keys())
    values = list(sub_industry_dist.values())
    colors = [SUB_INDUSTRY_COLORS.get(k, APPLE_GRAY) for k in labels]

    fig = go.Figure(
        data=go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
            textinfo="label+value",
            textfont=dict(size=12),
            hovertemplate="%{label}<br>企业数：%{value}<extra></extra>",
        )
    )
    fig.update_layout(
        annotations=[dict(text="产业<br>分布", x=0.5, y=0.5, font_size=16, showarrow=False)],
    )
    return _apple_layout(fig, "产业领域分布", height=400)


def build_industry_bar_chart(sub_industry_dist: Dict[str, int]) -> go.Figure:
    """产业分布横向条形图"""
    labels = list(sub_industry_dist.keys())
    values = list(sub_industry_dist.values())
    colors = [SUB_INDUSTRY_COLORS.get(k, APPLE_GRAY) for k in labels]

    fig = go.Figure(
        data=go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=colors, line=dict(color="#ffffff", width=1), cornerradius=6),
            text=[str(v) for v in values],
            textposition="outside",
            textfont=dict(size=12),
            hovertemplate="%{y}：%{x} 家<extra></extra>",
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)")
    fig.update_yaxes(showgrid=False, zeroline=False)
    return _apple_layout(fig, "产业领域企业数量", height=380)


def build_tier_pyramid_chart(tier_dist: Dict[str, int]) -> go.Figure:
    """企业梯队金字塔（倒序条形图，链主在顶部）"""
    order = ["配套服务企业", "科技型中小企业", "高新技术企业", "骨干企业", "链主企业"]
    labels = [t for t in order if tier_dist.get(t, 0) > 0]
    values = [tier_dist[t] for t in labels]
    colors = [APPLE_GRAY, APPLE_TEAL, APPLE_BLUE, APPLE_GREEN, APPLE_RED]

    fig = go.Figure(
        data=go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(
                color=colors[: len(labels)],
                line=dict(color="#ffffff", width=1),
                cornerradius=6,
            ),
            text=[str(v) for v in values],
            textposition="outside",
            textfont=dict(size=12),
            hovertemplate="%{y}：%{x} 家<extra></extra>",
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)")
    fig.update_yaxes(showgrid=False, zeroline=False, categoryorder="total ascending")
    return _apple_layout(fig, "企业梯队金字塔", height=360)


def build_chain_layer_chart(chain_dist: Dict[str, int]) -> go.Figure:
    """产业链层级分布图"""
    labels = ["上游", "中游", "下游"]
    values = [chain_dist.get(k, 0) for k in labels]
    colors = [APPLE_GREEN, APPLE_BLUE, APPLE_ORANGE]

    fig = go.Figure(
        data=go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors, line=dict(color="#ffffff", width=1), cornerradius=6),
            text=[str(v) for v in values],
            textposition="outside",
            textfont=dict(size=12),
            hovertemplate="%{x}：%{y} 家<extra></extra>",
        )
    )
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)")
    fig.update_xaxes(showgrid=False, zeroline=False)
    return _apple_layout(fig, "产业链层级分布", height=360)


def build_segment_strength_chart(
    segment_dist: Dict[str, Dict[str, Any]],
    segment_status: Dict[str, str],
) -> go.Figure:
    """产业链环节强度横向条形图"""
    # 按上中下游排序
    layer_order = {"上游": 0, "中游": 1, "下游": 2}
    segments = sorted(
        segment_dist.keys(),
        key=lambda s: (layer_order.get(segment_dist[s]["chain_position"], 99), -segment_dist[s]["count"]),
    )

    labels = segments
    values = [segment_dist[s]["count"] for s in segments]
    colors = [SEGMENT_STATUS_COLORS.get(segment_status.get(s, "正常"), APPLE_GRAY) for s in segments]

    fig = go.Figure(
        data=go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=colors, line=dict(color="#ffffff", width=1), cornerradius=6),
            text=[str(v) for v in values],
            textposition="outside",
            textfont=dict(size=11),
            hovertemplate="%{y}<br>企业数：%{x}<extra></extra>",
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", title="企业数量")
    fig.update_yaxes(showgrid=False, zeroline=False)
    return _apple_layout(fig, "产业链环节布局与强度", height=480)


def build_revenue_rd_scatter(enterprises: List[Dict[str, Any]]) -> go.Figure:
    """营收 vs 研发投入散点图"""
    x = [e.get("annual_revenue", 0) for e in enterprises]
    y = [e.get("rd_investment_ratio", 0) * 100 for e in enterprises]
    text = [e.get("name", "") for e in enterprises]
    colors = [SUB_INDUSTRY_COLORS.get(e.get("sub_industry"), APPLE_GRAY) for e in enterprises]
    sizes = [max(8, min(30, e.get("employees", 0) / 50)) for e in enterprises]

    fig = go.Figure(
        data=go.Scatter(
            x=x,
            y=y,
            mode="markers",
            text=text,
            marker=dict(
                color=colors,
                size=sizes,
                line=dict(color="#ffffff", width=1),
                opacity=0.8,
            ),
            hovertemplate="%{text}<br>营收：%{x} 亿元<br>研发占比：%{y:.1f}%<extra></extra>",
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", title="年产值（亿元）", type="log")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", title="研发投入占比（%）")
    return _apple_layout(fig, "营收与创新投入分布", height=420)


def build_top_enterprises_bar(enterprises: List[Dict[str, Any]], top_n: int = 10) -> go.Figure:
    """头部企业产值条形图"""
    sorted_ents = sorted(enterprises, key=lambda x: x.get("annual_revenue", 0), reverse=True)[:top_n]
    names = [e.get("name", "") for e in sorted_ents]
    revenues = [e.get("annual_revenue", 0) for e in sorted_ents]
    colors = [SUB_INDUSTRY_COLORS.get(e.get("sub_industry"), APPLE_GRAY) for e in sorted_ents]

    fig = go.Figure(
        data=go.Bar(
            x=revenues,
            y=names,
            orientation="h",
            marker=dict(color=colors, line=dict(color="#ffffff", width=1), cornerradius=6),
            text=[f"{v:.2f}" for v in revenues],
            textposition="outside",
            textfont=dict(size=11),
            hovertemplate="%{y}<br>营收：%{x} 亿元<extra></extra>",
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", title="年产值（亿元）")
    fig.update_yaxes(showgrid=False, zeroline=False, categoryorder="total ascending")
    return _apple_layout(fig, f"TOP{top_n} 企业年产值", height=420)


def build_innovation_density_chart(enterprises: List[Dict[str, Any]]) -> go.Figure:
    """产业创新密度气泡图：X=营收，Y=专利数，气泡大小=研发人员"""
    x = [e.get("annual_revenue", 0) for e in enterprises]
    y = [e.get("patents", 0) for e in enterprises]
    text = [e.get("name", "") for e in enterprises]
    colors = [SUB_INDUSTRY_COLORS.get(e.get("sub_industry"), APPLE_GRAY) for e in enterprises]
    sizes = [max(8, min(40, e.get("rd_personnel", 0) / 10)) for e in enterprises]

    fig = go.Figure(
        data=go.Scatter(
            x=x,
            y=y,
            mode="markers",
            text=text,
            marker=dict(
                color=colors,
                size=sizes,
                line=dict(color="#ffffff", width=1),
                opacity=0.8,
            ),
            hovertemplate="%{text}<br>营收：%{x} 亿元<br>专利：%{y} 项<extra></extra>",
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", title="年产值（亿元）", type="log")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", title="专利数量（项）")
    return _apple_layout(fig, "产业创新密度", height=420)


def build_chain_sankey(segment_dist: Dict[str, Dict[str, Any]]) -> go.Figure:
    """产业链层级桑基图（简化版）"""
    layers = {"上游": [], "中游": [], "下游": []}
    for seg, info in segment_dist.items():
        layer = info.get("chain_position", "中游")
        if layer in layers:
            layers[layer].append((seg, info["count"]))

    labels = []
    sources = []
    targets = []
    values = []

    # 节点：上游 + 中游 + 下游
    layer_nodes = {}
    for layer in ["上游", "中游", "下游"]:
        for seg, count in layers[layer]:
            layer_nodes[seg] = len(labels)
            labels.append(seg)

    # 简单连接：上游 -> 中游，中游 -> 下游
    for seg, count in layers["上游"]:
        for target_seg, target_count in layers["中游"]:
            sources.append(layer_nodes[seg])
            targets.append(layer_nodes[target_seg])
            values.append(min(count, target_count))

    for seg, count in layers["中游"]:
        for target_seg, target_count in layers["下游"]:
            sources.append(layer_nodes[seg])
            targets.append(layer_nodes[target_seg])
            values.append(min(count, target_count))

    fig = go.Figure(
        data=go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color=[APPLE_BLUE] * len(labels),
            ),
            link=dict(source=sources, target=targets, value=values),
        )
    )
    fig.update_layout(title_text="产业链层级流向", font_size=12, height=500)
    return fig
