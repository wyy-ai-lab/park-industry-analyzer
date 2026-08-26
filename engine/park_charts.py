"""
园区可视化图表
提供园区产业分析所需的 Plotly 图表组件。
"""

from typing import Dict, List, Any, Optional

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from engine.font_config import get_chart_font_family

CHART_FONT = get_chart_font_family()

# 投影增强配色（高对比度）
DEEP_BLUE = "#0056b3"   # 强势
BRIGHT_GREEN = "#34c759"  # 正常
ORANGE = "#ff9500"      # 薄弱
RED = "#ff3b30"         # 缺失
APPLE_GRAY = "#8e8e93"  # 服务支撑/未知
APPLE_PURPLE = "#af52de"
APPLE_TEAL = "#5ac8fa"

SEGMENT_STATUS_COLORS = {
    "强势": DEEP_BLUE,
    "正常": BRIGHT_GREEN,
    "薄弱": ORANGE,
    "缺失": RED,
    "服务支撑": APPLE_GRAY,
}

SUB_INDUSTRY_COLORS = {
    "动力电池": DEEP_BLUE,
    "电机电控": BRIGHT_GREEN,
    "智能网联": APPLE_PURPLE,
    "整车制造": RED,
    "充换电设施": ORANGE,
    "汽车服务": APPLE_TEAL,
    "其他配套": APPLE_GRAY,
}


def _apple_layout(
    fig: go.Figure,
    title: str,
    height: int = 420,
    annotation_text: Optional[str] = None,
) -> go.Figure:
    """统一应用 Apple 风格布局（投影优化版：大字、高对比）"""
    annotations = []
    if annotation_text:
        annotations.append(
            dict(
                text=annotation_text,
                x=0.5,
                y=-0.22,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=13, color="#6e6e73", family=CHART_FONT),
            )
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=19, color="#1d1d1f", family=CHART_FONT)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family=CHART_FONT,
            size=13,
            color="#1d1d1f",
        ),
        margin=dict(l=28, r=28, t=72, b=44 if annotation_text else 32),
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.5)",
            font=dict(size=13, family=CHART_FONT),
        ),
        annotations=annotations,
    )
    return fig


def build_industry_pie_chart(
    sub_industry_dist: Dict[str, int],
    height: int = 420,
    annotation_text: Optional[str] = None,
) -> go.Figure:
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
            textfont=dict(size=14, family=CHART_FONT),
            hovertemplate="%{label}<br>企业数：%{value}<extra></extra>",
        )
    )
    fig.update_layout(
        annotations=[
            dict(
                text="产业<br>分布",
                x=0.5,
                y=0.5,
                font_size=18,
                showarrow=False,
                font_color="#1d1d1f",
                font=dict(family=CHART_FONT),
            )
        ],
    )
    return _apple_layout(fig, "产业领域分布", height=height, annotation_text=annotation_text)


def build_industry_bar_chart(
    sub_industry_dist: Dict[str, int],
    height: int = 400,
) -> go.Figure:
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
            textfont=dict(size=13, family=CHART_FONT),
            hovertemplate="%{y}：%{x} 家<extra></extra>",
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", tickfont=dict(size=13, family=CHART_FONT), title=dict(text="企业数量", font=dict(size=14, family=CHART_FONT)))
    fig.update_yaxes(showgrid=False, zeroline=False, tickfont=dict(size=13, family=CHART_FONT))
    return _apple_layout(fig, "产业领域企业数量", height=height)


def build_tier_pyramid_chart(
    tier_dist: Dict[str, int],
    height: int = 380,
    annotation_text: Optional[str] = None,
) -> go.Figure:
    """企业梯队金字塔（倒序条形图，链主在顶部）"""
    order = ["配套服务企业", "科技型中小企业", "高新技术企业", "骨干企业", "链主企业"]
    labels = [t for t in order if tier_dist.get(t, 0) > 0]
    values = [tier_dist[t] for t in labels]
    colors = [APPLE_GRAY, APPLE_TEAL, DEEP_BLUE, BRIGHT_GREEN, RED]

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
            textfont=dict(size=13, family=CHART_FONT),
            hovertemplate="%{y}：%{x} 家<extra></extra>",
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", tickfont=dict(size=13, family=CHART_FONT))
    fig.update_yaxes(showgrid=False, zeroline=False, categoryorder="total ascending", tickfont=dict(size=13, family=CHART_FONT))
    return _apple_layout(fig, "企业梯队金字塔", height=height, annotation_text=annotation_text)


def build_chain_layer_chart(
    chain_dist: Dict[str, int],
    height: int = 380,
    annotation_text: Optional[str] = None,
) -> go.Figure:
    """产业链层级分布图"""
    labels = ["上游", "中游", "下游"]
    values = [chain_dist.get(k, 0) for k in labels]
    colors = [BRIGHT_GREEN, DEEP_BLUE, ORANGE]

    fig = go.Figure(
        data=go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors, line=dict(color="#ffffff", width=1), cornerradius=6),
            text=[str(v) for v in values],
            textposition="outside",
            textfont=dict(size=13, family=CHART_FONT),
            hovertemplate="%{x}：%{y} 家<extra></extra>",
        )
    )
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", tickfont=dict(size=13, family=CHART_FONT), title=dict(text="企业数量", font=dict(size=14, family=CHART_FONT)))
    fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(size=13, family=CHART_FONT))
    return _apple_layout(fig, "产业链层级分布", height=height, annotation_text=annotation_text)


def build_segment_strength_chart(
    segment_dist: Dict[str, Dict[str, Any]],
    segment_status: Dict[str, str],
    height: int = 520,
    annotation_text: Optional[str] = None,
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
            textfont=dict(size=12, family=CHART_FONT),
            hovertemplate="%{y}<br>企业数：%{x}<extra></extra>",
        )
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.06)",
        title=dict(text="企业数量", font=dict(size=14, family=CHART_FONT)),
        tickfont=dict(size=13, family=CHART_FONT),
    )
    fig.update_yaxes(showgrid=False, zeroline=False, tickfont=dict(size=13, family=CHART_FONT))
    return _apple_layout(fig, "产业链环节布局与强度", height=height, annotation_text=annotation_text)


def build_revenue_rd_scatter(
    enterprises: List[Dict[str, Any]],
    height: int = 440,
) -> go.Figure:
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
    fig.update_xaxes(
        showgrid=True, gridcolor="rgba(0,0,0,0.06)",
        title=dict(text="年产值（亿元）", font=dict(size=14, family=CHART_FONT)),
        tickfont=dict(size=13, family=CHART_FONT), type="log",
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="rgba(0,0,0,0.06)",
        title=dict(text="研发投入占比（%）", font=dict(size=14, family=CHART_FONT)),
        tickfont=dict(size=13, family=CHART_FONT),
    )
    return _apple_layout(fig, "营收与创新投入分布", height=height)


def build_top_enterprises_bar(
    enterprises: List[Dict[str, Any]],
    top_n: int = 10,
    height: int = 440,
    annotation_text: Optional[str] = None,
) -> go.Figure:
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
            textfont=dict(size=12, family=CHART_FONT),
            hovertemplate="%{y}<br>营收：%{x} 亿元<extra></extra>",
        )
    )
    fig.update_xaxes(
        showgrid=True, gridcolor="rgba(0,0,0,0.06)",
        title=dict(text="年产值（亿元）", font=dict(size=14, family=CHART_FONT)),
        tickfont=dict(size=13, family=CHART_FONT),
    )
    fig.update_yaxes(showgrid=False, zeroline=False, categoryorder="total ascending", tickfont=dict(size=12, family=CHART_FONT))
    return _apple_layout(fig, f"TOP{top_n} 企业年产值", height=height, annotation_text=annotation_text)


def build_innovation_density_chart(
    enterprises: List[Dict[str, Any]],
    height: int = 440,
) -> go.Figure:
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
    fig.update_xaxes(
        showgrid=True, gridcolor="rgba(0,0,0,0.06)",
        title=dict(text="年产值（亿元）", font=dict(size=14, family=CHART_FONT)),
        tickfont=dict(size=13, family=CHART_FONT), type="log",
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="rgba(0,0,0,0.06)",
        title=dict(text="专利数量（项）", font=dict(size=14, family=CHART_FONT)),
        tickfont=dict(size=13, family=CHART_FONT),
    )
    return _apple_layout(fig, "产业创新密度", height=height)


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

    layer_nodes = {}
    for layer in ["上游", "中游", "下游"]:
        for seg, count in layers[layer]:
            layer_nodes[seg] = len(labels)
            labels.append(seg)

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
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=[DEEP_BLUE] * len(labels),
        )
    )
    fig.update_layout(
        title_text="产业链层级流向",
        font=dict(family=CHART_FONT, size=13),
        height=500,
    )
    return fig


def fig_to_image_bytes(fig, format: str = "png", width: int = 900, scale: int = 2) -> bytes:
    """
    将 Plotly 图表转为图片 bytes。

    默认使用已安装的 kaleido。部分 Plotly/Kaleido 版本组合不支持 engine 参数，
    因此先尝试不传 engine，失败后再尝试显式指定 kaleido。
    """
    import plotly.io as pio

    try:
        return pio.to_image(fig, format=format, width=width, scale=scale)
    except TypeError:
        return pio.to_image(fig, format=format, width=width, scale=scale, engine="kaleido")
