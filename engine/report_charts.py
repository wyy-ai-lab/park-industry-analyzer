"""
诊断报告图表组件

提供用于「诊断报告」页面的 Plotly 可视化：
- 诊断结果分布饼图
- TOP3 政策申报时间线图
- 企业能力维度条形图
- 高频差距/缺失项条形图
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Apple 主题色（与 UI 保持一致）
DIAGNOSIS_COLORS = {
    "立即申报": "#34c759",
    "培育申报": "#ff9500",
    "持续关注": "#0071e3",
    "暂不适合": "#ff3b30",
}

DIMENSION_COLORS = [
    "#0071e3", "#34c759", "#ff9500", "#af52de", "#5856d6", "#5ac8fa"
]


def _apple_layout(fig: go.Figure, title: str, height: int = 420) -> go.Figure:
    """统一应用 Apple 风格布局"""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#1d1d1f")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, sans-serif", color="#1d1d1f"),
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


def build_diagnosis_pie_chart(summary_counts: Dict[str, int]) -> go.Figure:
    """
    诊断结果分布环形图
    """
    labels = ["立即申报", "培育申报", "持续关注", "暂不适合"]
    values = [summary_counts.get(k, 0) for k in labels]
    colors = [DIAGNOSIS_COLORS[k] for k in labels]

    # 过滤掉数量为 0 的类别，避免图例冗余
    active = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if not active:
        active = [("暂无数据", 1, "#d1d1d6")]

    labels_f, values_f, colors_f = zip(*active)

    fig = go.Figure(
        data=go.Pie(
            labels=labels_f,
            values=values_f,
            hole=0.58,
            marker=dict(colors=colors_f, line=dict(color="#ffffff", width=2)),
            textinfo="label+value",
            textfont=dict(size=13),
            hovertemplate="%{label}<br>数量：%{value}<extra></extra>",
        )
    )
    fig.update_layout(
        annotations=[dict(text="诊断<br>分布", x=0.5, y=0.5, font_size=16, showarrow=False)],
    )
    return _apple_layout(fig, "诊断结果分布", height=360)


def build_timeline_chart(top3_policies: List[Dict[str, Any]]) -> go.Figure:
    """
    TOP3 政策申报时间线（甘特风格）

    以当前日期为起点，截止日为终点绘制横向条形；
    无截止日的政策按类别给出建议周期。
    """
    if not top3_policies:
        fig = go.Figure()
        fig.add_annotation(
            text="暂无推荐政策",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#6e6e73"),
        )
        return _apple_layout(fig, "TOP3 政策申报时间线", height=280)

    today = datetime.now()
    tasks = []
    for p in top3_policies:
        deadline_str = p.get("deadline", "")
        try:
            end = datetime.strptime(deadline_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            diagnosis = p.get("diagnosis", "")
            if diagnosis == "立即申报":
                end = today + timedelta(days=30)
            elif diagnosis == "培育申报":
                end = today + timedelta(days=365)
            else:
                end = today + timedelta(days=90)

        # 保证至少 7 天可见
        if (end - today).days < 7:
            end = today + timedelta(days=7)

        tasks.append({
            "name": f"{p['rank']}. {p['policy_name']}",
            "start": today,
            "end": end,
            "diagnosis": p.get("diagnosis", ""),
            "deadline": deadline_str,
        })

    fig = go.Figure()
    y_positions = list(range(len(tasks) - 1, -1, -1))

    for i, task in enumerate(tasks):
        color = DIAGNOSIS_COLORS.get(task["diagnosis"], "#0071e3")
        hover_text = (
            f"{task['name']}<br>"
            f"诊断：{task['diagnosis']}<br>"
            f"截止：{task['deadline'] or '无固定截止日'}"
        )
        fig.add_trace(go.Scatter(
            x=[task["start"], task["end"]],
            y=[y_positions[i], y_positions[i]],
            mode="lines",
            line=dict(color=color, width=16),
            hovertemplate=hover_text + "<extra></extra>",
            showlegend=False,
        ))
        # 起点标记
        fig.add_trace(go.Scatter(
            x=[task["start"]],
            y=[y_positions[i]],
            mode="markers",
            marker=dict(color=color, size=10, symbol="circle"),
            hoverinfo="skip",
            showlegend=False,
        ))
        # 终点标记
        fig.add_trace(go.Scatter(
            x=[task["end"]],
            y=[y_positions[i]],
            mode="markers+text",
            marker=dict(color=color, size=12, symbol="diamond"),
            text=[task["deadline"] or "—"],
            textposition="middle right",
            textfont=dict(size=11, color="#1d1d1f"),
            hoverinfo="skip",
            showlegend=False,
        ))

    fig.update_yaxes(
        tickvals=y_positions,
        ticktext=[t["name"] for t in tasks],
        showgrid=False,
        zeroline=False,
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.06)",
        zeroline=False,
        tickformat="%m-%d",
        title="时间线（今天 → 截止日）",
    )

    return _apple_layout(fig, "TOP3 政策申报时间线", height=320)


def build_capability_bar_chart(capability_scores: Dict[str, int]) -> go.Figure:
    """
    企业能力维度横向条形图
    """
    dims = list(capability_scores.keys())
    scores = list(capability_scores.values())
    colors = [DIMENSION_COLORS[i % len(DIMENSION_COLORS)] for i in range(len(dims))]

    fig = go.Figure(
        data=go.Bar(
            x=scores,
            y=dims,
            orientation="h",
            marker=dict(
                color=colors,
                line=dict(color="#ffffff", width=1),
                cornerradius=6,
            ),
            text=[f"{s} 分" for s in scores],
            textposition="outside",
            textfont=dict(size=12),
            hovertemplate="%{y}：%{x} 分<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, 100], showgrid=True, gridcolor="rgba(0,0,0,0.06)")
    fig.update_yaxes(showgrid=False, zeroline=False)
    return _apple_layout(fig, "企业能力维度得分", height=360)


def build_gap_bar_chart(top_gaps: List[tuple]) -> go.Figure:
    """
    高频差距/缺失项横向条形图
    """
    if not top_gaps:
        fig = go.Figure()
        fig.add_annotation(
            text="未发现显著高频差距项",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#6e6e73"),
        )
        return _apple_layout(fig, "高频差距/缺失项", height=260)

    labels = [g[0] for g in top_gaps]
    counts = [g[1] for g in top_gaps]

    fig = go.Figure(
        data=go.Bar(
            x=counts,
            y=labels,
            orientation="h",
            marker=dict(color="#ff3b30", line=dict(color="#ffffff", width=1), cornerradius=6),
            text=[str(c) for c in counts],
            textposition="outside",
            textfont=dict(size=12),
            hovertemplate="%{y}：%{x} 项<extra></extra>",
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)")
    fig.update_yaxes(showgrid=False, zeroline=False)
    return _apple_layout(fig, "高频差距/缺失项 TOP5", height=280)
