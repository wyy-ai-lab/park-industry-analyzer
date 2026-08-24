import streamlit as st
from engine.ui_helpers import inject_apple_theme

st.set_page_config(
    page_title="园区产业分析智能体",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_apple_theme()

st.markdown("""
<style>
/* 首页减少顶部 padding */
.block-container {
    padding-top: 2rem !important;
}

.home-hero {
    text-align: center;
    padding: 3rem 1rem 2.5rem;
}
.home-hero-title {
    font-size: 3.2rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin-bottom: 0.75rem;
    background: linear-gradient(135deg, #1d1d1f 0%, #5e5e60 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.home-hero-subtitle {
    font-size: 1.3rem;
    font-weight: 400;
    color: var(--apple-muted);
    letter-spacing: 0.02em;
}

.home-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    padding: 2rem 1.5rem;
    height: 100%;
    transition: transform 0.35s cubic-bezier(0.25, 0.1, 0.25, 1), box-shadow 0.35s cubic-bezier(0.25, 0.1, 0.25, 1);
}
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
    .home-card {
        background: var(--apple-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
}
.home-card:hover {
    transform: translateY(-6px);
    box-shadow: var(--shadow-lg);
}
.home-card-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}
.home-card-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--apple-text);
    margin-bottom: 0.5rem;
    letter-spacing: -0.01em;
    text-decoration: none;
    display: inline-block;
    transition: color 0.25s ease;
}
a.home-card-title:hover,
a.home-card-title:focus {
    color: var(--apple-blue);
    text-decoration: none;
}
.home-card-desc {
    font-size: 0.92rem;
    color: var(--apple-muted);
    margin-bottom: 1.25rem;
    line-height: 1.55;
}
.capability-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1rem;
}
.capability-grid-item {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow-sm);
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
    .capability-grid-item {
        background: var(--apple-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
}
.capability-grid-item:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.capability-grid-icon {
    font-size: 1.4rem;
    line-height: 1;
}
.capability-grid-text {
    font-size: 0.92rem;
    color: var(--apple-text);
    line-height: 1.5;
    font-weight: 500;
}

@media (max-width: 640px) {
    .home-hero-title { font-size: 2.1rem; }
    .home-hero-subtitle { font-size: 1rem; }
    .capability-grid { grid-template-columns: 1fr; }
    .home-card { padding: 1.5rem 1.25rem; }
}
</style>
""", unsafe_allow_html=True)

# Hero
st.markdown("""
<div class="home-hero">
    <div class="home-hero-title">🏭 园区产业分析智能体</div>
    <div class="home-hero-subtitle">看清园区产业全局 · 识别产业链强弱 · 下钻企业诊断</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='text-align: center; margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

# 快速入口
st.markdown('<div class="home-quick-links">', unsafe_allow_html=True)

cards = [
    ("🏞️", "1_园区概览", "园区概览", "掌握园区核心经济指标、企业总数、产值与高新技术企业分布。"),
    ("🗺️", "2_产业地图", "产业地图", "产业领域分布、企业梯队金字塔、创新密度与主导产业识别。"),
    ("🕸️", "3_产业链图谱", "产业链图谱", "产业链环节布局、强弱缺失分析、断链风险与补链建议。"),
    ("🔍", "4_企业透视", "企业透视", "搜索筛选园区企业，查看详情并一键进入单个企业诊断辅导。"),
    ("💡", "5_发展建议", "发展建议", "基于园区数据生成结构化诊断结论、招商与培育建议。"),
    ("🩺", "6_企业诊断辅导", "企业诊断辅导", "复用企业政策诊断能力：画像、诊断、报告、培育路线图。"),
]

rows = [cards[i:i+3] for i in range(0, len(cards), 3)]
for row in rows:
    cols = st.columns(len(row))
    for col, (icon, page, title, desc) in zip(cols, row):
        with col:
            st.markdown(f"""
            <div class="home-card">
                <div class="home-card-icon">{icon}</div>
                <a href="{page}" class="home-card-title">{title}</a>
                <div class="home-card-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# 当前能力
st.subheader("✅ 当前能力")

st.markdown("""
<div class="capability-grid">
    <div class="capability-grid-item">
        <div class="capability-grid-icon">🏞️</div>
        <div class="capability-grid-text">园区产业概览：核心指标、产业分布、头部企业</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">🗺️</div>
        <div class="capability-grid-text">产业地图：梯队金字塔、产业链层级、创新密度</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">🕸️</div>
        <div class="capability-grid-text">产业链图谱：完整度、本地配套率、强弱缺失分析</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">🔍</div>
        <div class="capability-grid-text">企业透视：50 家演示企业搜索、筛选、下钻诊断</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">💡</div>
        <div class="capability-grid-text">发展建议：LLM / 模板生成招商补链与培育建议</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">🩺</div>
        <div class="capability-grid-text">企业诊断辅导：硬条件 + LLM 软条件综合诊断与报告导出</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">📊</div>
        <div class="capability-grid-text">可视化：Plotly 交互图表，Apple 风格主题</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">🌐</div>
        <div class="capability-grid-text">LLM 可选：支持 Anthropic / OpenAI，演示模式免 API Key</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.info("👈 也可以直接点击左侧菜单栏进入各页面")
