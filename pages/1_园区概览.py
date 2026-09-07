import json
import os

import pandas as pd
import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.park_metrics import load_park_enterprises, compute_metrics
from engine.park_llm import generate_diagnosis
from engine.park_charts import build_industry_pie_chart, build_top_enterprises_bar

st.set_page_config(
    page_title="园区概览 - 政策-产业-企业智能体",
    page_icon="🏞️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_apple_theme()

# 汇报模式切换
presentation_mode = st.toggle("🎤 汇报模式", key="park_presentation_mode")

# 条件样式
if presentation_mode:
    st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--apple-text);
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }
    .help-text { display: none; }
    .metric-card {
        background: var(--apple-card-solid);
        border: 1px solid var(--apple-border);
        border-radius: var(--radius-lg);
        padding: 2rem 1.25rem;
        box-shadow: var(--shadow-sm);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    .metric-value {
        font-size: 2.6rem;
        font-weight: 700;
        color: var(--apple-text);
        letter-spacing: -0.02em;
    }
    .metric-label {
        font-size: 1rem;
        color: var(--apple-muted);
        margin-top: 0.5rem;
    }
    .section-title {
        font-size: 1.35rem;
        font-weight: 600;
        color: var(--apple-text);
        margin-bottom: 1rem;
        padding-bottom: 0.65rem;
        border-bottom: 1px solid var(--apple-border);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .insight-card {
        background: var(--apple-card-solid);
        border: 1px solid var(--apple-border);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
        height: 100%;
    }
    .insight-card h4 {
        margin: 0 0 0.75rem;
        font-size: 1.15rem;
        color: var(--apple-text);
    }
    .insight-card ul {
        margin: 0;
        padding-left: 1.2rem;
        color: var(--apple-text);
        line-height: 1.8;
        font-size: 1.05rem;
    }
    .insight-card li {
        margin-bottom: 0.4rem;
    }
    .conclusion-bar {
        background: var(--apple-card-solid);
        border: 1px solid var(--apple-border);
        border-radius: var(--radius-lg);
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-sm);
        font-size: 1.25rem;
        font-weight: 500;
        color: var(--apple-text);
        line-height: 1.6;
        text-align: center;
    }
    .intro-card {
        background: var(--apple-card-solid);
        border: 1px solid var(--apple-border);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .main-title {
        font-size: 1.9rem;
        font-weight: 700;
        color: var(--apple-text);
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }
    .help-text {
        color: var(--apple-muted);
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: var(--apple-card-solid);
        border: 1px solid var(--apple-border);
        border-radius: var(--radius-lg);
        padding: 1.1rem 1.25rem;
        box-shadow: var(--shadow-sm);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--apple-text);
        letter-spacing: -0.02em;
    }
    .metric-label {
        font-size: 0.85rem;
        color: var(--apple-muted);
        margin-top: 0.25rem;
    }
    .section-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: var(--apple-text);
        margin-bottom: 1rem;
        padding-bottom: 0.65rem;
        border-bottom: 1px solid var(--apple-border);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .intro-card {
        background: var(--apple-card-solid);
        border: 1px solid var(--apple-border);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">🏞️ 园区概览</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">看清园区产业全局，掌握核心经济指标与企业分布。</div>', unsafe_allow_html=True)

# 加载数据
data = load_park_enterprises()
if not data or not data.get("enterprises"):
    if st.session_state.get("use_demo_data", True):
        st.warning("⚠️ 未找到园区企业数据，请确认 `data/park_enterprises.json` 存在。")
    else:
        st.warning("📦 演示数据已关闭，当前为「未接入数据」状态。返回首页打开左侧开关「载入演示数据」即可查看演示内容。")
    st.stop()

metrics = compute_metrics(data)
park_name = metrics.get("park_name", "未知园区")

# 园区信息可编辑，默认填充当前案例数据
default_profile = {
    "park_name": park_name,
    "dominant_industry": "新能源汽车",
    "park_intro": (
        f"**{park_name}** 是以新能源汽车为主导产业的园区，涵盖动力电池、电机电控、智能网联、"
        "整车制造、充换电设施及汽车服务等全产业链环节。园区依托合肥市汽车产业基础，"
        "形成了以动力电池电芯、整车制造为核心的产业格局，是区域新能源汽车产业的重要承载地。"
    ),
    "total_enterprises": int(metrics.get("total_enterprises", 0)),
    "total_revenue": float(metrics["totals"]["total_revenue"]),
    "total_employees": int(metrics["totals"]["total_employees"]),
    "high_tech_count": int(metrics["totals"]["high_tech_count"]),
    "little_giant_count": int(metrics["totals"]["little_giant_count"]),
}
if "park_profile" not in st.session_state:
    st.session_state["park_profile"] = default_profile

profile = st.session_state["park_profile"]

# 汇报模式：获取或生成诊断结论
if presentation_mode:
    if "park_diagnosis" not in st.session_state or st.session_state.get("regenerate_diagnosis"):
        with st.spinner("正在生成园区诊断结论..."):
            st.session_state["park_diagnosis"] = generate_diagnosis(metrics)
            st.session_state["regenerate_diagnosis"] = False
    diagnosis = st.session_state.get("park_diagnosis", {})

    # 核心结论
    top_sub_industries = sorted(
        metrics.get("sub_industry_distribution", {}).items(),
        key=lambda x: x[1],
        reverse=True,
    )[:2]
    core_sub = "、".join([k for k, _ in top_sub_industries]) if top_sub_industries else "主导产业"
    conclusion = (
        f"{profile['park_name']}已形成以{core_sub}为核心的产业格局，"
        f"产业链完整度 {metrics.get('completeness_score', 0)} 分，"
        f"本地配套率 {metrics.get('local_support_rate', 0)}%。"
    )
    st.markdown(f'<div class="conclusion-bar">{conclusion}</div>', unsafe_allow_html=True)

# 编辑园区信息
st.markdown('<div class="section-title">✏️ 编辑园区信息</div>', unsafe_allow_html=True)
st.caption("当前已预填演示案例数据，修改后仅影响本页展示。")
with st.container(border=True):
    with st.form("park_profile_form"):
        edit_col1, edit_col2 = st.columns(2)
        with edit_col1:
            new_name = st.text_input("园区名称", value=profile["park_name"])
            new_industry = st.text_input("主导产业", value=profile["dominant_industry"])
            new_total = st.number_input("企业总数", min_value=0, value=int(profile["total_enterprises"]))
            new_revenue = st.number_input("年产值（亿元）", min_value=0.0, value=float(profile["total_revenue"]))
        with edit_col2:
            new_employees = st.number_input("员工总数", min_value=0, value=int(profile["total_employees"]))
            new_high_tech = st.number_input("高新技术企业数", min_value=0, value=int(profile["high_tech_count"]))
            new_little = st.number_input("小巨人企业数", min_value=0, value=int(profile["little_giant_count"]))
        new_intro = st.text_area("园区简介", value=profile["park_intro"], height=120)

        submitted = st.form_submit_button("💾 保存修改", type="primary", use_container_width=True)
        if submitted:
            st.session_state["park_profile"] = {
                "park_name": new_name,
                "dominant_industry": new_industry,
                "park_intro": new_intro,
                "total_enterprises": new_total,
                "total_revenue": new_revenue,
                "total_employees": new_employees,
                "high_tech_count": new_high_tech,
                "little_giant_count": new_little,
            }
            st.success("✅ 园区信息已更新")
            st.rerun()

# 园区简介
with st.container(border=True):
    st.markdown(f'<div class="section-title">📍 {profile["park_name"]}</div>', unsafe_allow_html=True)
    intro_col1, intro_col2 = st.columns([2, 1])
    with intro_col1:
        st.markdown(profile["park_intro"])
    with intro_col2:
        st.markdown(f"""
        - **企业总数**：{profile['total_enterprises']} 家
        - **年产值**：约 {profile['total_revenue']:.1f} 亿元
        - **员工总数**：约 {profile['total_employees']:,} 人
        - **高新技术企业**：{profile['high_tech_count']} 家
        """)

# 核心指标卡片
st.markdown('<div class="section-title">📊 核心指标</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
cards = [
    ("企业总数", f"{profile['total_enterprises']} 家", c1),
    ("年产值", f"{profile['total_revenue']:.1f} 亿元", c2),
    ("员工总数", f"{profile['total_employees']:,} 人", c3),
    ("高新技术企业", f"{profile['high_tech_count']} 家", c4),
    ("小巨人企业", f"{profile['little_giant_count']} 家", c5),
]
for label, value, col in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

# 汇报模式：核心洞察卡片
if presentation_mode:
    st.markdown('<div class="section-title">💡 核心洞察</div>', unsafe_allow_html=True)
    insight_col1, insight_col2, insight_col3 = st.columns(3)

    strengths = diagnosis.get("core_strengths", [])[:3]
    gaps = diagnosis.get("key_gaps", [])[:3]
    next_focus = []
    next_focus.extend(diagnosis.get("investment_suggestions", [])[:2])
    next_focus.extend(diagnosis.get("cultivation_suggestions", [])[:2])
    next_focus = next_focus[:3]

    with insight_col1:
        items_html = "".join(f"<li>{s}</li>" for s in strengths) if strengths else "<li>暂无</li>"
        st.markdown(f"""
        <div class="insight-card">
            <h4>✅ 核心优势</h4>
            <ul>{items_html}</ul>
        </div>
        """, unsafe_allow_html=True)

    with insight_col2:
        items_html = "".join(f"<li>{g}</li>" for g in gaps) if gaps else "<li>暂无</li>"
        st.markdown(f"""
        <div class="insight-card">
            <h4>⚠️ 关键短板</h4>
            <ul>{items_html}</ul>
        </div>
        """, unsafe_allow_html=True)

    with insight_col3:
        items_html = "".join(f"<li>{n}</li>" for n in next_focus) if next_focus else "<li>暂无</li>"
        st.markdown(f"""
        <div class="insight-card">
            <h4>🎯 下一步重点</h4>
            <ul>{items_html}</ul>
        </div>
        """, unsafe_allow_html=True)

# 产业分布与头部企业
st.divider()
dist_col, top_col = st.columns([1, 1.2])
chart_height = 520 if presentation_mode else 420
with dist_col:
    st.markdown('<div class="section-title">🏭 产业分布</div>', unsafe_allow_html=True)
    annotation = f"产业链完整度 {metrics.get('completeness_score', 0)} 分"
    fig_pie = build_industry_pie_chart(
        metrics["sub_industry_distribution"],
        height=chart_height,
        annotation_text=annotation,
    )
    st.plotly_chart(fig_pie, use_container_width=True, key="overview_pie")

with top_col:
    st.markdown('<div class="section-title">🏆 头部企业（按年产值）</div>', unsafe_allow_html=True)
    fig_top = build_top_enterprises_bar(
        data["enterprises"],
        top_n=10,
        height=chart_height,
    )
    st.plotly_chart(fig_top, use_container_width=True, key="overview_top")

# 梯队与层级
st.divider()
tier_col, chain_col = st.columns(2)
with tier_col:
    st.markdown('<div class="section-title">📈 企业梯队</div>', unsafe_allow_html=True)
    tier_df = pd.DataFrame([
        {"梯队": k, "企业数": v}
        for k, v in metrics["tier_distribution"].items()
    ])
    st.dataframe(tier_df, use_container_width=True, hide_index=True)

with chain_col:
    st.markdown('<div class="section-title">🔗 产业链层级</div>', unsafe_allow_html=True)
    chain_df = pd.DataFrame([
        {"层级": k, "企业数": v}
        for k, v in metrics["chain_distribution"].items()
    ])
    st.dataframe(chain_df, use_container_width=True, hide_index=True)

if not presentation_mode:
    st.info("💡 提示：点击左侧菜单可进入产业地图、产业链图谱、企业透视等页面查看详情。")
