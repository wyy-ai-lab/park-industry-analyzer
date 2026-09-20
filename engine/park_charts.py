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


def build_health_radar_chart(dimensions: Dict[str, float], height: int = 380) -> go.Figure:
    """产业健康指数雷达图：当前园区 vs 满分基准"""
    labels = list(dimensions.keys())
    values = [dimensions[k] for k in labels]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + values[:1],
        theta=labels + labels[:1],
        fill="toself",
        fillcolor="rgba(0,113,227,0.18)",
        line=dict(color="#0071e3", width=2.5),
        name="本园区",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[100] * (len(labels) + 1),
        theta=labels + labels[:1],
        line=dict(color="#8e8e93", width=1.5, dash="dot"),
        name="满分基准",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 100], tickfont=dict(size=11), gridcolor="#e5e5ea"),
            angularaxis=dict(tickfont=dict(size=13, family=CHART_FONT)),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=CHART_FONT, color="#1d1d1f"),
        margin=dict(l=40, r=40, t=30, b=30),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, x=0.5, xanchor="center"),
        showlegend=True,
    )
    return fig


def build_metric_trend_chart(trends: Dict[str, Any], height: int = 380) -> go.Figure:
    """近三年核心指标趋势：产值（左轴）+ 完整度/配套率（右轴）"""
    years = trends.get("years", [])

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=years, y=trends.get("revenue", []),
            mode="lines+markers+text", text=[f"{v:.0f}" for v in trends.get("revenue", [])],
            textposition="top center", line=dict(color="#0071e3", width=3),
            marker=dict(size=9), name="总产值（亿元）",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=trends.get("completeness", []),
            mode="lines+markers", line=dict(color="#34c759", width=2.5, dash="dash"),
            marker=dict(size=8), name="产业链完整度（分）",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=trends.get("support_rate", []),
            mode="lines+markers", line=dict(color="#ff9500", width=2.5, dash="dot"),
            marker=dict(size=8), name="本地配套率（%）",
        ),
        secondary_y=True,
    )
    fig.update_xaxes(tickmode="array", tickvals=years, ticktext=[str(y) for y in years])
    fig.update_yaxes(title_text="总产值（亿元）", secondary_y=False, rangemode="tozero")
    fig.update_yaxes(title_text="分数 / 百分比", secondary_y=True, range=[0, 105])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=CHART_FONT, size=13, color="#1d1d1f"),
        margin=dict(l=28, r=28, t=40, b=32),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, x=0.5, xanchor="center"),
    )
    return fig


def build_supply_network_chart(enterprises: List[Dict[str, Any]], height: int = 560) -> go.Figure:
    """
    企业供需网络图：节点按产业链层级布局（上游 → 下游），
    边表示供货/客户关系；园区外主体显示为灰色空心节点（对外依赖）。
    """
    layer_x = {"上游": 0.0, "中游": 1.0, "下游": 2.0}
    palette = {"上游": "#5ac8fa", "中游": "#0071e3", "下游": "#34c759"}

    # 按层级、产值排序确定纵向位置
    by_layer: Dict[str, List[Dict[str, Any]]] = {"上游": [], "中游": [], "下游": []}
    for e in enterprises:
        layer = e.get("chain_position", "中游")
        if layer not in by_layer:
            by_layer[layer] = []
        by_layer[layer].append(e)
    for layer in by_layer:
        by_layer[layer].sort(key=lambda x: -x.get("annual_revenue", 0))

    pos: Dict[str, Dict[str, Any]] = {}
    for layer, ents in by_layer.items():
        n = len(ents)
        for i, e in enumerate(ents):
            y = (n - 1) / 2 - i  # 从上到下按产值降序
            jitter = (hash(e.get("niche", "")) % 7 - 3) * 0.04
            pos[e["name"]] = {
                "x": layer_x.get(layer, 1.0) + jitter,
                "y": y,
                "layer": layer,
                "niche": e.get("niche", ""),
                "revenue": e.get("annual_revenue", 0),
            }

    # 边：本地供应商（绿）> 上游供货（蓝）> 下游客户（橙）
    edges = []
    for e in enterprises:
        src = e["name"]
        for tgt in e.get("local_suppliers", []) or []:
            if tgt and tgt != src:
                edges.append((src, tgt, "本地配套", "#34c759"))
        for tgt in e.get("upstream_suppliers", []) or []:
            if tgt and tgt != src and not any(t[1] == tgt for t in edges if t[0] == src):
                edges.append((src, tgt, "上游供货", "#0071e3"))
        for tgt in e.get("downstream_customers", []) or []:
            if tgt and tgt != src:
                edges.append((src, tgt, "下游客户", "#ff9500"))

    # 园区外依赖节点
    ext_names = sorted({t for _, t, _, _ in edges if t not in pos})

    edge_x, edge_y = [], []
    for src, tgt, rel, color in edges:
        if src not in pos or tgt not in pos:
            continue
        edge_x += [pos[src]["x"], pos[tgt]["x"], None]
        edge_y += [pos[src]["y"], pos[tgt]["y"], None]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="rgba(142,142,147,0.45)", width=1.2),
        hoverinfo="skip", showlegend=False,
    ))

    for layer in ("上游", "中游", "下游"):
        names = [k for k, p in pos.items() if p["layer"] == layer]
        fig.add_trace(go.Scatter(
            x=[pos[n]["x"] for n in names],
            y=[pos[n]["y"] for n in names],
            mode="markers+text",
            text=[n.split("有限公司")[0].replace("股份有限公司", "").replace("有限责任公司", "")[:6] for n in names],
            textposition="middle center",
            textfont=dict(size=9, color="#ffffff", family=CHART_FONT),
            marker=dict(size=34, color=palette[layer], opacity=0.92, line=dict(color="#ffffff", width=1.5)),
            name=f"{layer}（{len(names)} 家）",
            hovertext=[
                f"{n}<br>{pos[n]['niche']} · 年产值 {pos[n]['revenue']:.1f} 亿元" for n in names
            ],
            hoverinfo="text",
        ))

    if ext_names:
        ext_x = [2.45 + (i % 2) * 0.12 for i in range(len(ext_names))]
        ext_y = [(len(ext_names) - 1) / 2 - i for i in range(len(ext_names))]
        fig.add_trace(go.Scatter(
            x=ext_x, y=ext_y, mode="markers+text",
            text=[n if len(n) <= 8 else n[:8] + "…" for n in ext_names],
            textposition="middle right",
            textfont=dict(size=10, color="#8e8e93", family=CHART_FONT),
            marker=dict(size=22, color="rgba(142,142,147,0.25)",
                        line=dict(color="#8e8e93", width=1.2)),
            name=f"园区外依赖（{len(ext_names)} 家）",
            hovertext=ext_names, hoverinfo="text",
        ))

    fig.update_layout(
        title=dict(text="企业供需网络（左：上游 → 右：下游）", font=dict(size=16, family=CHART_FONT, color="#1d1d1f")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=CHART_FONT, size=12, color="#1d1d1f"),
        margin=dict(l=20, r=20, t=50, b=20),
        height=height,
        xaxis=dict(visible=False, range=[-0.45, 3.4]),
        yaxis=dict(visible=False),
        legend=dict(orientation="h", yanchor="bottom", y=-0.06, x=0.5, xanchor="center"),
    )
    return fig


def build_tech_track_chart(tracks: List[Dict[str, Any]], height: int = 460) -> go.Figure:
    """技术赛道气泡图：x=平均产业链层级，气泡大小=发明专利数，颜色=产值"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[t["avg_layer"] for t in tracks],
        y=[t["track"] for t in tracks],
        mode="markers+text",
        text=[t["track"] for t in tracks],
        textposition="middle center",
        textfont=dict(size=12, color="#ffffff", family=CHART_FONT),
        marker=dict(
            size=[max(26, t["invention_patents"] / 3) for t in tracks],
            sizemode="diameter",
            color=[t["revenue"] for t in tracks],
            colorscale="Blues",
            showscale=True,
            colorbar=dict(title="产值（亿元）"),
            opacity=0.9,
            line=dict(color="#ffffff", width=1.5),
        ),
        hovertext=[
            f"{t['track']}：{t['count']} 家企业 · 发明专利 {t['invention_patents']} 项<br>"
            f"核心技术：{'、'.join(t['core_techs']) or '—'}<br>代表企业：{t['top_enterprise']}"
            for t in tracks
        ],
        hoverinfo="text",
        showlegend=False,
    ))
    fig.update_xaxes(
        tickvals=[1, 2, 3], ticktext=["上游", "中游", "下游"],
        range=[0.4, 3.6], title="平均产业链层级",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=CHART_FONT, size=13, color="#1d1d1f"),
        margin=dict(l=28, r=28, t=40, b=40),
        height=height,
    )
    return fig
