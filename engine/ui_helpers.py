"""
UI 辅助组件
用于在多页面间统一展示步骤指示器、引导提示等
"""

import os
import streamlit as st


# 页面顺序定义
PAGE_ORDER = [
    {"key": "profile", "label": "企业画像", "icon": "🏢", "page": "pages/1_企业画像.py"},
    {"key": "diagnosis", "label": "政策诊断", "icon": "🔍", "page": "pages/2_政策诊断.py"},
    {"key": "report", "label": "诊断报告", "icon": "📋", "page": "pages/3_诊断报告.py"},
]


# Apple 风格全局主题 CSS
APPLE_THEME_CSS = """
<style>
/* ===== Apple 风格设计系统 ===== */
:root {
    --apple-bg: #f5f5f7;
    --apple-card: rgba(255, 255, 255, 0.82);
    --apple-card-solid: #ffffff;
    --apple-text: #1d1d1f;
    --apple-muted: #6e6e73;
    --apple-border: rgba(0, 0, 0, 0.08);
    --apple-blue: #0071e3;
    --apple-blue-dark: #0077ed;
    --apple-blue-light: rgba(0, 113, 227, 0.12);
    --apple-green: #34c759;
    --apple-green-light: rgba(52, 199, 89, 0.12);
    --apple-orange: #ff9500;
    --apple-orange-light: rgba(255, 149, 0, 0.12);
    --apple-red: #ff3b30;
    --apple-red-light: rgba(255, 59, 48, 0.12);
    --apple-purple: #af52de;
    --apple-indigo: #5856d6;
    --apple-teal: #5ac8fa;
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.04);
    --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.08);
    --shadow-lg: 0 20px 48px rgba(0, 0, 0, 0.12);
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 20px;
    --radius-pill: 9999px;
}

/* 页面全局 */
.stApp {
    background: var(--apple-bg) !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji" !important;
}

/* 顶部主内容区增加 padding，避免被粘性步骤条遮挡 */
.block-container {
    padding-top: 7rem !important;
    padding-bottom: 3rem !important;
}

/* 标题类 */
.apple-hero {
    text-align: center;
    padding: 2.5rem 1rem 2rem;
}
.apple-hero-title {
    font-size: 3rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--apple-text);
    margin-bottom: 0.75rem;
    background: linear-gradient(135deg, #1d1d1f 0%, #434344 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.apple-hero-subtitle {
    font-size: 1.25rem;
    font-weight: 400;
    color: var(--apple-muted);
    letter-spacing: 0.02em;
}

/* 卡片通用 */
.apple-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    transition: transform 0.3s cubic-bezier(0.25, 0.1, 0.25, 1), box-shadow 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
}
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
    .apple-card {
        background: var(--apple-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
}
.apple-card:hover {
    transform: translateY(-6px);
    box-shadow: var(--shadow-lg);
}

/* 药丸标签 */
.apple-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem 1.1rem;
    border-radius: var(--radius-pill);
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    box-shadow: var(--shadow-sm);
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--apple-text);
}

/* 按钮统一样式（药丸形） */
.stButton > button {
    border-radius: var(--radius-pill) !important;
    font-weight: 500 !important;
    padding: 0.55rem 1.5rem !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(0, 113, 227, 0.25) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* 主按钮 */
.stButton > button[kind="primary"] {
    background: var(--apple-blue) !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--apple-blue-dark) !important;
}

/* 次按钮 */
.stButton > button[kind="secondary"] {
    background: var(--apple-card-solid) !important;
    color: var(--apple-text) !important;
    border: 1px solid var(--apple-border) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #f9f9fb !important;
}

/* 输入框美化 */
.stTextInput input,
.stNumberInput input,
.stSelectbox > div > div,
.stMultiselect > div > div,
.stSlider > div > div > div {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--apple-border) !important;
    background: var(--apple-card-solid) !important;
    color: var(--apple-text) !important;
}
.stTextInput input:focus,
.stNumberInput input:focus,
.stSelectbox > div > div:focus-within,
.stMultiselect > div > div:focus-within {
    border-color: var(--apple-blue) !important;
    box-shadow: 0 0 0 4px var(--apple-blue-light) !important;
}

/* 侧边栏 */
[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.72) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid var(--apple-border) !important;
}

/* 通用标题 */
.main-title {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--apple-text);
    margin-bottom: 0.5rem;
}
.section-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    padding: 1.5rem;
    margin-bottom: 1.25rem;
}
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
    .section-card {
        background: var(--apple-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
}
.section-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--apple-text);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.help-text {
    color: var(--apple-muted);
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}

/* 响应式 */
@media (max-width: 640px) {
    .apple-hero-title { font-size: 2rem; }
    .apple-hero-subtitle { font-size: 1rem; }
    .block-container { padding-top: 6rem !important; }
}
</style>
"""


def inject_apple_theme():
    """注入 Apple 风格全局主题 CSS"""
    st.markdown(APPLE_THEME_CSS, unsafe_allow_html=True)


# 步骤指示器 CSS
STEP_INDICATOR_CSS = """
<style>
.step-bar-wrapper {
    position: sticky;
    top: 0;
    z-index: 999;
    padding: 0.6rem 0;
    margin-bottom: 0.75rem;
    background: var(--apple-bg);
    border-bottom: 1px solid var(--apple-border);
}
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
    .step-bar-wrapper {
        background: rgba(245, 245, 247, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }
}
.step-bar {
    max-width: 720px;
    margin: 0 auto;
    padding: 0;
    background: transparent;
    border: none;
    box-shadow: none;
}
.app-header { text-align: center; margin-bottom: 0.75rem; }
.app-name {
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--apple-text);
}
.app-tagline {
    font-size: 0.85rem;
    font-weight: 400;
    color: var(--apple-muted);
    margin-top: 0.15rem;
}
.step-indicator { display: flex; align-items: center; justify-content: center; padding: 0.25rem 0 0; }
.step-item { display: flex; flex-direction: column; align-items: center; min-width: 110px; }
.step-shape {
    width: 64px;
    height: 64px;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    margin-bottom: 0.6rem;
    transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
}
.step-label { font-size: 0.95rem; font-weight: 600; letter-spacing: -0.01em; }
.step-current .step-shape {
    background: var(--apple-blue);
    color: white;
    box-shadow: 0 0 0 6px var(--apple-blue-light);
}
.step-current .step-label { color: var(--apple-blue); font-weight: 700; }
.step-completed .step-shape { background: var(--apple-green); color: white; }
.step-completed .step-label { color: var(--apple-green); font-weight: 600; }
.step-pending .step-shape { background: #e5e5ea; color: #8e8e93; }
.step-pending .step-label { color: var(--apple-muted); }
.step-line {
    flex: 1;
    height: 3px;
    max-width: 100px;
    margin: 0 0.75rem;
    margin-bottom: 2.4rem;
    border-radius: 2px;
    transition: all 0.4s ease;
}
.step-line-completed {
    background: linear-gradient(90deg, #e5e5ea 0%, var(--apple-green) 50%, var(--apple-blue) 100%);
}
.step-line-pending { background: #e5e5ea; }

@media (max-width: 640px) {
    .step-bar-wrapper { padding: 0.5rem 0; }
    .app-name { font-size: 1rem; }
    .app-tagline { font-size: 0.8rem; }
    .step-item { min-width: 86px; }
    .step-shape { width: 52px; height: 52px; border-radius: 14px; font-size: 1.3rem; }
    .step-label { font-size: 0.85rem; }
    .step-line { max-width: 40px; margin-bottom: 2rem; }
}
</style>
"""


def render_step_indicator(current_page: str):
    """
    在页面顶部渲染产品标题和 Apple 风格步骤指示器

    current_page 取值："profile" / "diagnosis" / "report"
    """
    page_index = {p["key"]: i for i, p in enumerate(PAGE_ORDER)}
    current_idx = page_index.get(current_page, 0)

    steps_html = []
    for i, page in enumerate(PAGE_ORDER):
        is_current = i == current_idx
        is_completed = i < current_idx

        if is_current:
            state_class = "step-current"
            icon = page["icon"]
        elif is_completed:
            state_class = "step-completed"
            icon = "✓"
        else:
            state_class = "step-pending"
            icon = page["icon"]

        steps_html.append(
            f'<div class="step-item {state_class}">'
            f'<div class="step-shape">{icon}</div>'
            f'<div class="step-label">{page["label"]}</div>'
            f'</div>'
        )

        if i < len(PAGE_ORDER) - 1:
            line_class = "step-line-completed" if is_completed else "step-line-pending"
            steps_html.append(f'<div class="step-line {line_class}"></div>')

    html_content = STEP_INDICATOR_CSS.strip() + """
<div class="step-bar-wrapper">
    <div class="step-bar">
        <div class="app-header">
            <div class="app-name">🤖 企业政策诊断辅导智能体</div>
            <div class="app-tagline">发现政策 · 诊断差距 · 辅导申报 · 生成材料</div>
        </div>
        <div class="step-indicator">""" + "".join(steps_html) + """</div>
    </div>
</div>
"""

    st.markdown(html_content, unsafe_allow_html=True)


def check_prerequisite(prerequisite: str, current_page: str) -> bool:
    """
    检查前置条件是否满足。

    prerequisite:
        - "enterprise": 需要 data/enterprise.json
        - "diagnosis": 需要 output/diagnosis_result.json

    返回 True 表示满足；False 表示未满足，并显示引导提示。
    """
    if prerequisite == "enterprise":
        if not os.path.exists("data/enterprise.json"):
            render_step_indicator(current_page)
            st.warning("⚠️ 请先完成「企业画像」填写")
            if st.button("🏢 前往企业画像", type="primary"):
                st.switch_page("pages/1_企业画像.py")
            return False

    elif prerequisite == "diagnosis":
        if not os.path.exists("output/diagnosis_result.json"):
            render_step_indicator(current_page)
            st.warning("⚠️ 请先前往「政策诊断」页面运行诊断")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏢 填写企业画像", type="secondary"):
                    st.switch_page("pages/1_企业画像.py")
            with col2:
                if st.button("🔍 前往政策诊断", type="primary"):
                    st.switch_page("pages/2_政策诊断.py")
            return False

    return True
