import pandas as pd
import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.park_metrics import load_park_enterprises, compute_metrics
from engine.park_charts import (
    build_industry_bar_chart,
    build_tier_pyramid_chart,
    build_chain_layer_chart,
    build_revenue_rd_scatter,
    build_innovation_density_chart,
)

st.set_page_config(
    page_title="产业地图 - 园区产业分析智能体",
    page_icon="🗺️",
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
.leading-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    box-shadow: var(--shadow-sm);
    height: 100%;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.leading-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.leading-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--apple-text);
    margin-bottom: 0.5rem;
}
.leading-desc {
    font-size: 0.9rem;
    color: var(--apple-muted);
    line-height: 1.5;
}
.leading-stat {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--apple-blue);
    margin-top: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🗺️ 产业地图</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">产业集群分布、企业梯队与创新密度分析。</div>', unsafe_allow_html=True)

# 加载数据
data = load_park_enterprises()
if not data or not data.get("enterprises"):
    if st.session_state.get("use_demo_data", True):
        st.warning("⚠️ 未找到园区企业数据，请确认 `data/park_enterprises.json` 存在。")
    else:
        st.warning("📦 演示数据已关闭，当前为「未接入数据」状态。返回首页打开左侧开关「载入演示数据」即可查看演示内容。")
    st.stop()

metrics = compute_metrics(data)

# 产业分布
st.markdown('<div class="section-title">🏭 产业领域分布</div>', unsafe_allow_html=True)
industry_col1, industry_col2 = st.columns([1.2, 1])
with industry_col1:
    fig_bar = build_industry_bar_chart(metrics["sub_industry_distribution"])
    st.plotly_chart(fig_bar, use_container_width=True, key="map_bar")
with industry_col2:
    st.markdown("**产业产值估算**")
    revenue_by_industry = {}
    for e in data["enterprises"]:
        sub = e.get("sub_industry", "未知")
        revenue_by_industry[sub] = revenue_by_industry.get(sub, 0) + e.get("annual_revenue", 0)
    revenue_df = pd.DataFrame([
        {"产业领域": k, "年产值（亿元）": round(v, 2), "企业数": metrics["sub_industry_distribution"].get(k, 0)}
        for k, v in sorted(revenue_by_industry.items(), key=lambda x: -x[1])
    ])
    st.dataframe(revenue_df, use_container_width=True, hide_index=True)

st.divider()

# 企业梯队 + 产业链层级
pyramid_col, layer_col = st.columns([1, 1])
with pyramid_col:
    st.markdown('<div class="section-title">📊 企业梯队金字塔</div>', unsafe_allow_html=True)
    fig_pyramid = build_tier_pyramid_chart(metrics["tier_distribution"])
    st.plotly_chart(fig_pyramid, use_container_width=True, key="map_pyramid")

with layer_col:
    st.markdown('<div class="section-title">🔗 产业链层级分布</div>', unsafe_allow_html=True)
    fig_layer = build_chain_layer_chart(metrics["chain_distribution"])
    st.plotly_chart(fig_layer, use_container_width=True, key="map_layer")

st.divider()

# 创新密度
st.markdown('<div class="section-title">🔬 创新密度分析</div>', unsafe_allow_html=True)
scatter_col, bubble_col = st.columns(2)
with scatter_col:
    st.markdown("**营收 vs 研发投入占比**")
    fig_scatter = build_revenue_rd_scatter(data["enterprises"])
    st.plotly_chart(fig_scatter, use_container_width=True, key="map_scatter")
with bubble_col:
    st.markdown("**营收 vs 专利数（气泡大小=研发人员）**")
    fig_bubble = build_innovation_density_chart(data["enterprises"])
    st.plotly_chart(fig_bubble, use_container_width=True, key="map_bubble")

st.divider()

# 主导产业卡片
st.markdown('<div class="section-title">🌟 主导产业识别</div>', unsafe_allow_html=True)
sub_dist = metrics["sub_industry_distribution"]
revenue_by_industry = {}
for e in data["enterprises"]:
    sub = e.get("sub_industry", "未知")
    revenue_by_industry[sub] = revenue_by_industry.get(sub, 0) + e.get("annual_revenue", 0)

# 按企业数和产值综合排序
leading = sorted(
    sub_dist.keys(),
    key=lambda k: (sub_dist.get(k, 0) * 0.4 + revenue_by_industry.get(k, 0) * 0.6),
    reverse=True,
)[:4]

cards = st.columns(4)
desc_map = {
    "动力电池": "园区核心优势产业，覆盖正负极材料、电芯、电池包集成等关键环节。",
    "电机电控": "骨干企业聚集，驱动电机与电控系统配套能力较强。",
    "智能网联": "高成长性产业，车载操作系统、高精地图等软件能力突出。",
    "整车制造": "链主企业带动，乘用车与商用车制造协同发展。",
    "充换电设施": "服务配套完善，充电桩、换电站、运营平台布局完整。",
    "汽车服务": "后市场服务体系逐步完善，金融与回收环节初具规模。",
    "其他配套": "生产设备与检测设备等产业支撑能力。",
}
for col, sub in zip(cards, leading):
    with col:
        st.markdown(f"""
        <div class="leading-card">
            <div class="leading-title">{sub}</div>
            <div class="leading-desc">{desc_map.get(sub, '')}</div>
            <div class="leading-stat">{sub_dist.get(sub, 0)} 家 · {revenue_by_industry.get(sub, 0):.1f} 亿</div>
        </div>
        """, unsafe_allow_html=True)

st.info("💡 提示：主导产业根据企业数量和年产值综合识别，反映园区当前产业重心。")
