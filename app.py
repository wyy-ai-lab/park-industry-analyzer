"""
园区产业分析智能体 · 首页
==========================
导航宿主：st.navigation 三段式信息架构

- 主入口：产业智能梳理（材料 → 分类 → 环节 → 路径 → 清单 → 资源）
- 演示园区 · 示例数据：原有五个演示分析页（50 家示例企业）
- 企业服务：单企业诊断辅导
"""

import textwrap

import streamlit as st
from engine.ui_helpers import inject_apple_theme, render_demo_controls

st.set_page_config(
    page_title="园区产业分析智能体",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
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

.home-entry {
    display: block;
    background: linear-gradient(135deg, #0052D9 0%, #2B7FFF 100%);
    border-radius: var(--radius-lg);
    padding: 1.75rem 2rem;
    color: #fff;
    text-decoration: none;
    box-shadow: var(--shadow-md);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    margin-bottom: 1.25rem;
}
a.home-entry-link { text-decoration: none; }
a.home-entry-link:hover .home-entry {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg, 0 12px 32px rgba(0, 82, 217, 0.25));
}
.home-entry-title {
    font-size: 1.35rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.home-entry-desc {
    font-size: 0.92rem;
    opacity: 0.92;
    margin-top: 0.45rem;
    line-height: 1.6;
}
.home-entry-cta {
    display: inline-block;
    margin-top: 0.85rem;
    font-size: 0.88rem;
    font-weight: 600;
    background: rgba(255, 255, 255, 0.18);
    border: 1px solid rgba(255, 255, 255, 0.35);
    padding: 0.35rem 1rem;
    border-radius: 999px;
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


def home():
    """首页：一句话价值主张 + 一个主入口 + 两个次要入口。"""
    # Hero
    st.markdown(textwrap.dedent("""
    <div class="home-hero">
        <div class="home-hero-title">🏭 园区产业分析智能体</div>
        <div class="home-hero-subtitle">
            粘贴一份园区企业材料，自动完成产业分类、上中下游环节诊断、强链补链延链路径与招商资源梳理。
        </div>
    </div>
    """), unsafe_allow_html=True)

    # 主入口
    st.markdown(textwrap.dedent("""
    <a href="产业智能梳理" class="home-entry-link">
        <div class="home-entry">
            <div class="home-entry-title">🧭 产业智能梳理 <span style="font-size:0.8rem;font-weight:500;opacity:0.85">主入口</span></div>
            <div class="home-entry-desc">上传企业目录、园区介绍等基础材料，自动完成产业分类 → 上中下游分环节梳理 →
            强弱缺失诊断 → 强链补链延链路径 → 招商目标企业清单 + 研究院/协会资源。</div>
            <div class="home-entry-cta">开始梳理 →</div>
        </div>
    </a>
    """), unsafe_allow_html=True)

    # 两个次要入口
    sec_col1, sec_col2 = st.columns(2)
    with sec_col1:
        st.markdown(textwrap.dedent("""
        <a href="园区概览" class="home-card-link">
            <div class="home-card">
                <div class="home-card-icon">🚗</div>
                <div class="home-card-title">演示园区 · 示例数据</div>
                <div class="home-card-desc">内置合肥高新区新能源汽车产业园 50 家示例企业，
                体验园区概览、产业地图、产业链图谱、发展建议与企业透视等分析模块。</div>
            </div>
        </a>
        """), unsafe_allow_html=True)
    with sec_col2:
        st.markdown(textwrap.dedent("""
        <a href="企业诊断辅导" class="home-card-link">
            <div class="home-card">
                <div class="home-card-icon">🩺</div>
                <div class="home-card-title">企业诊断辅导</div>
                <div class="home-card-desc">针对单个企业做政策匹配诊断：画像 → 政策诊断 → 报告导出 → 培育路线图。</div>
            </div>
        </a>
        """), unsafe_allow_html=True)

    # Footer
    st.markdown(textwrap.dedent("""
    <div class="home-footer">
        园区产业分析智能体 · Demo 版本 · 基于 Streamlit 构建<br>
        演示模块数据为示例数据，仅供能力演示；产业智能梳理支持上传真实材料
    </div>
    """), unsafe_allow_html=True)


# ---------------------------------------------------------------- 三段式导航
# 极简三入口：演示分析页（园区概览等）不在侧边栏出现，
# 经首页「演示园区」卡片进入园区概览后横向跳转。
NAV_SECTIONS = {
    "": [
        st.Page(home, title="首页", icon="🏠", default=True),
        st.Page("pages/7_产业智能梳理.py", title="产业智能梳理", icon="🧭",
                url_path="产业智能梳理"),
    ],
    "企业服务": [
        st.Page("pages/6_企业诊断辅导.py", title="企业诊断辅导", icon="🩺", url_path="企业诊断辅导"),
    ],
}

from engine.auth import require_auth, render_auth_controls


def render_sidebar_nav() -> None:
    """自定义侧边栏层级导航（替代 st.navigation 默认侧栏）。

    一级：园区服务（产业智能梳理）/ 企业服务（企业诊断辅导）
    二级：可点开的步骤列表——梳理页走锚点跳转，诊断页走 switch_page + 标签定位。
    """
    with st.sidebar:
        st.markdown(
            '<div style="font-size:0.9rem;margin-bottom:0.35rem">'
            '<a href="首页">🏠 首页</a></div>',
            unsafe_allow_html=True)

        st.markdown('<div style="font-size:0.75rem;color:var(--apple-muted);'
                    'font-weight:600;margin:0.5rem 0 0.15rem">园区服务</div>',
                    unsafe_allow_html=True)
        with st.expander("🧭 产业智能梳理", expanded=True):
            st.markdown(
                '<div style="font-size:0.85rem;line-height:2">'
                '<a href="产业智能梳理#ia-sec-material">提供园区材料</a><br>'
                '<a href="产业智能梳理#ia-sec-classify">产业分类</a><br>'
                '<a href="产业智能梳理#ia-sec-chain">产业链上下游分析</a><br>'
                '<a href="产业智能梳理#ia-sec-advice">产业发展建议</a><br>'
                '<a href="产业智能梳理#ia-sec-invest">产业招商推荐</a></div>',
                unsafe_allow_html=True)

        st.markdown('<div style="font-size:0.75rem;color:var(--apple-muted);'
                    'font-weight:600;margin:0.6rem 0 0.15rem">企业服务</div>',
                    unsafe_allow_html=True)
        with st.expander("🩺 企业诊断辅导"):
            for label, tab_key in (("企业画像录入", "profile"), ("运行政策诊断", "diagnosis"),
                                   ("诊断报告分析", "report"), ("企业培育路线", "roadmap")):
                if st.button(label, key=f"nav_diag_{tab_key}",
                             use_container_width=True):
                    st.session_state["enterprise_active_tab"] = tab_key
                    st.switch_page("pages/6_企业诊断辅导.py")
        st.divider()


nav = st.navigation(NAV_SECTIONS, position="hidden")
require_auth()
render_sidebar_nav()
nav.run()
# 全局控件放最后：自定义导航 + 页面级侧边栏内容优先展示
render_auth_controls()
render_demo_controls()
