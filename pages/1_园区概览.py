import json
import os

import pandas as pd
import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.park_metrics import load_park_enterprises, compute_metrics
from engine.park_charts import build_industry_pie_chart, build_top_enterprises_bar

st.set_page_config(
    page_title="园区概览 - 园区产业分析智能体",
    page_icon="🏞️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_apple_theme()

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
    st.warning("⚠️ 未找到园区企业数据，请确认 `data/park_enterprises.json` 存在。")
    st.stop()

metrics = compute_metrics(data)
park_name = metrics.get("park_name", "未知园区")

# 园区简介
with st.container(border=True):
    st.markdown(f'<div class="section-title">📍 {park_name}</div>', unsafe_allow_html=True)
    intro_col1, intro_col2 = st.columns([2, 1])
    with intro_col1:
        st.markdown(f"""
        **{park_name}** 是以新能源汽车为主导产业的园区，涵盖动力电池、电机电控、智能网联、
        整车制造、充换电设施及汽车服务等全产业链环节。园区依托合肥市汽车产业基础，
        形成了以动力电池电芯、整车制造为核心的产业格局，是区域新能源汽车产业的重要承载地。
        """)
    with intro_col2:
        st.markdown(f"""
        - **企业总数**：{metrics['total_enterprises']} 家
        - **年产值**：约 {metrics['totals']['total_revenue']:.1f} 亿元
        - **员工总数**：约 {metrics['totals']['total_employees']:,} 人
        - **高新技术企业**：{metrics['totals']['high_tech_count']} 家
        """)

# 核心指标卡片
st.markdown('<div class="section-title">📊 核心指标</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
cards = [
    ("企业总数", f"{metrics['totals']['enterprise_count']} 家", c1),
    ("年产值", f"{metrics['totals']['total_revenue']:.1f} 亿元", c2),
    ("员工总数", f"{metrics['totals']['total_employees']:,} 人", c3),
    ("高新技术企业", f"{metrics['totals']['high_tech_count']} 家", c4),
    ("小巨人企业", f"{metrics['totals']['little_giant_count']} 家", c5),
]
for label, value, col in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

# 产业分布与头部企业
st.divider()
dist_col, top_col = st.columns([1, 1.2])
with dist_col:
    st.markdown('<div class="section-title">🏭 产业分布</div>', unsafe_allow_html=True)
    fig_pie = build_industry_pie_chart(metrics["sub_industry_distribution"])
    st.plotly_chart(fig_pie, use_container_width=True, key="overview_pie")

with top_col:
    st.markdown('<div class="section-title">🏆 头部企业（按年产值）</div>', unsafe_allow_html=True)
    fig_top = build_top_enterprises_bar(data["enterprises"], top_n=10)
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

st.info("💡 提示：点击左侧菜单可进入产业地图、产业链图谱、企业透视等页面查看详情。")
