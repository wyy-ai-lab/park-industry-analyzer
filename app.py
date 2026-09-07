import re
import textwrap

import streamlit as st
from engine.ui_helpers import inject_apple_theme
from engine.park_metrics import load_park_enterprises, compute_metrics

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
    padding: 2.5rem 1rem 1.5rem;
}
.home-hero-title {
    font-size: 3rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin-bottom: 0.75rem;
    background: linear-gradient(135deg, #1d1d1f 0%, #5e5e60 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.home-hero-subtitle {
    font-size: 1.25rem;
    font-weight: 400;
    color: var(--apple-muted);
    letter-spacing: 0.02em;
    max-width: 640px;
    margin: 0 auto;
    line-height: 1.6;
}

.home-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    max-width: 900px;
    margin: 1.5rem auto 2rem;
}
.home-stat-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1.25rem 0.75rem;
    text-align: center;
    box-shadow: var(--shadow-sm);
}
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
    .home-stat-card {
        background: var(--apple-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
}
.home-stat-value {
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--apple-blue);
    letter-spacing: -0.02em;
}
.home-stat-label {
    font-size: 0.82rem;
    color: var(--apple-muted);
    margin-top: 0.35rem;
    font-weight: 500;
}

.home-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    padding: 1.5rem;
    height: 100%;
    position: relative;
    overflow: hidden;
    transition: transform 0.3s cubic-bezier(0.25, 0.1, 0.25, 1), box-shadow 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
}
.home-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--apple-blue), var(--apple-teal));
}
.home-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-md);
}
a.home-card-link {
    display: block;
    text-decoration: none;
    color: inherit;
}
a.home-card-link:hover .home-card {
    transform: translateY(-5px);
    box-shadow: var(--shadow-md);
}
.home-card-icon {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    margin-bottom: 1rem;
    background: var(--apple-blue-light);
}
.home-card-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--apple-text);
    margin-bottom: 0.5rem;
    letter-spacing: -0.01em;
}
.home-card-desc {
    font-size: 0.9rem;
    color: var(--apple-muted);
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
.capability-grid-item:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.capability-grid-icon {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    flex-shrink: 0;
}
.capability-grid-text {
    font-size: 0.92rem;
    color: var(--apple-text);
    line-height: 1.5;
    font-weight: 500;
}

.home-footer {
    text-align: center;
    color: var(--apple-muted);
    font-size: 0.8rem;
    margin-top: 3rem;
    padding: 1.5rem 0;
    border-top: 1px solid var(--apple-border);
}

@media (max-width: 768px) {
    .home-hero-title { font-size: 2.2rem; }
    .home-hero-subtitle { font-size: 1rem; }
    .home-stats { grid-template-columns: repeat(2, 1fr); }
    .home-stat-value { font-size: 1.5rem; }
    .home-card { padding: 1.25rem; }
}
</style>
""", unsafe_allow_html=True)

# 侧边栏品牌头
st.sidebar.markdown(textwrap.dedent("""
<div class="sidebar-brand">
    <div class="sidebar-brand-icon">🏭</div>
    <div class="sidebar-brand-title">园区产业分析</div>
    <div class="sidebar-brand-tagline">智能体 v1.0 · Demo</div>
</div>
"""), unsafe_allow_html=True)

# 侧边栏：演示数据开关（用于演示“未接入数据 → 载入数据”的过程）
st.sidebar.divider()
st.sidebar.toggle(
    "📦 载入演示数据（50 家企业）",
    value=True,
    key="use_demo_data",
    help="关闭后，全站将模拟“尚未接入园区企业数据”的空状态。",
)

# 加载园区指标，用于首页数据看板
try:
    park_data = load_park_enterprises()
    park_metrics = compute_metrics(park_data) if park_data else {}
except Exception:
    park_data = {}
    park_metrics = {}

# 是否已接入园区企业数据：未接入时不展示虚构指标，只显示占位符
has_park_data = bool(park_data and park_data.get("enterprises"))

if has_park_data:
    total_enterprises = park_metrics.get("total_enterprises", 0)
    completeness = park_metrics.get("completeness_score", 0)
    local_support = park_metrics.get("local_support_rate", 0)
    stat_enterprise = f"{total_enterprises}"
    stat_completeness = f"{completeness:.1f}"
    stat_support = f"{local_support:.1f}%"
else:
    stat_enterprise = "—"
    stat_completeness = "—"
    stat_support = "—"

# Hero
st.markdown(textwrap.dedent(f"""
<div class="home-hero">
    <div class="home-hero-title">🏭 园区产业分析智能体</div>
    <div class="home-hero-subtitle">
        看清园区产业全局 · 识别产业链强弱 · 下钻企业诊断<br>
        为园区管委会提供数据驱动的产业洞察与招商培育建议
    </div>
</div>
"""), unsafe_allow_html=True)

# 核心数据条
st.markdown(textwrap.dedent(f"""
<div class="home-stats">
    <div class="home-stat-card">
        <div class="home-stat-value">{stat_enterprise}</div>
        <div class="home-stat-label">园区企业</div>
    </div>
    <div class="home-stat-card">
        <div class="home-stat-value">6</div>
        <div class="home-stat-label">分析模块</div>
    </div>
    <div class="home-stat-card">
        <div class="home-stat-value">{stat_completeness}</div>
        <div class="home-stat-label">产业链完整度</div>
    </div>
    <div class="home-stat-card">
        <div class="home-stat-value">{stat_support}</div>
        <div class="home-stat-label">本地配套率</div>
    </div>
</div>
"""), unsafe_allow_html=True)

# 未接入数据时的空状态提示
if not has_park_data:
    if st.session_state.get("use_demo_data", True):
        st.info("ℹ️ 尚未接入园区企业数据，园区类指标暂不可计算。请先在「园区概览」页录入园区信息，或上传企业台账数据后，首页指标将自动更新。")
    else:
        st.info("📦 演示数据已关闭，当前为「未接入数据」状态。打开左侧开关「载入演示数据」，即可查看演示园区的完整分析。")

st.divider()

# 快速入口
st.subheader("🚀 快速入口")

quick_links = [
    ("🏞️", "pages/1_园区概览.py", "园区概览", "核心经济指标、产业分布、头部企业一览"),
    ("🗺️", "pages/2_产业地图.py", "产业地图", "梯队金字塔、产业链层级、创新密度"),
    ("🕸️", "pages/3_产业链图谱.py", "产业链图谱", "完整度、本地配套率、强弱缺失分析"),
    ("🔍", "pages/4_企业透视.py", "企业透视", "50 家演示企业搜索、筛选、下钻诊断"),
    ("💡", "pages/5_发展建议.py", "发展建议", "LLM / 模板生成招商补链与培育建议"),
    ("🩺", "pages/6_企业诊断辅导.py", "企业诊断辅导", "单企业画像、政策诊断、报告导出"),
]

rows = [quick_links[i:i+3] for i in range(0, len(quick_links), 3)]
for row in rows:
    cols = st.columns(len(row))
    for col, (icon, page, title, desc) in zip(cols, row):
        with col:
            page_label = re.sub(r"^\d+_", "", page.rsplit("/", 1)[-1].replace(".py", ""))
            st.markdown(textwrap.dedent(f"""
            <a href="{page_label}" class="home-card-link">
                <div class="home-card">
                    <div class="home-card-icon">{icon}</div>
                    <div class="home-card-title">{title}</div>
                    <div class="home-card-desc">{desc}</div>
                </div>
            </a>
            """), unsafe_allow_html=True)

st.divider()

# Footer
st.markdown(textwrap.dedent("""
<div class="home-footer">
    园区产业分析智能体 · Demo 版本 · 基于 Streamlit 构建<br>
    数据为演示数据，仅供内部汇报使用
</div>
"""), unsafe_allow_html=True)
