import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.park_metrics import load_park_enterprises, compute_metrics
from engine.park_llm import generate_diagnosis

st.set_page_config(
    page_title="发展建议 - 园区产业分析智能体",
    page_icon="💡",
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
.assessment-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    box-shadow: var(--shadow-sm);
    margin-bottom: 1rem;
}
.assessment-card h4 {
    margin: 0 0 0.75rem;
    font-size: 1rem;
    color: var(--apple-text);
}
.assessment-card ul {
    margin: 0;
    padding-left: 1.2rem;
    color: var(--apple-text);
    line-height: 1.7;
}
.badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 500;
    background: var(--apple-blue-light);
    color: var(--apple-blue);
}
.risk-card {
    background: rgba(255, 59, 48, 0.08);
    border: 1px solid rgba(255, 59, 48, 0.3);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    box-shadow: var(--shadow-sm);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">💡 发展建议</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">基于园区产业数据生成结构化诊断结论与发展建议。</div>', unsafe_allow_html=True)

# 加载数据
data = load_park_enterprises()
if not data or not data.get("enterprises"):
    st.warning("⚠️ 未找到园区企业数据，请确认 `data/park_enterprises.json` 存在。")
    st.stop()

metrics = compute_metrics(data)

# 生成或复用诊断结论
if "park_diagnosis" not in st.session_state or st.session_state.get("regenerate_diagnosis"):
    with st.status("正在生成园区产业诊断结论...", expanded=True) as status:
        diagnosis = generate_diagnosis(metrics)
        st.session_state["park_diagnosis"] = diagnosis
        st.session_state["regenerate_diagnosis"] = False
        mode_label = "LLM" if diagnosis.get("mode") == "llm" else "模板"
        status.update(label=f"诊断已生成（{diagnosis.get('provider', 'demo')} / {mode_label}）", state="complete")

diagnosis = st.session_state["park_diagnosis"]

# 顶部操作栏
header_col, action_col = st.columns([4, 1])
with header_col:
    mode_text = "LLM 生成" if diagnosis.get("mode") == "llm" else "规则模板"
    st.markdown(f"<span class='badge'>{diagnosis.get('provider', 'demo')} · {mode_text}</span>", unsafe_allow_html=True)
with action_col:
    if st.button("🔄 重新生成诊断", use_container_width=True):
        st.session_state["regenerate_diagnosis"] = True
        st.rerun()

st.divider()

# 整体判断
st.markdown('<div class="section-title">📋 整体判断</div>', unsafe_allow_html=True)
st.info(diagnosis.get("overall_assessment", "暂无整体判断"))

# 核心优势 & 关键短板
col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="assessment-card"><h4>✅ 核心优势</h4>', unsafe_allow_html=True)
    strengths = diagnosis.get("core_strengths", [])
    if strengths:
        st.markdown("<ul>" + "".join(f"<li>{s}</li>" for s in strengths) + "</ul>", unsafe_allow_html=True)
    else:
        st.markdown("<p>暂无</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="assessment-card"><h4>⚠️ 关键短板</h4>', unsafe_allow_html=True)
    gaps = diagnosis.get("key_gaps", [])
    if gaps:
        st.markdown("<ul>" + "".join(f"<li>{g}</li>" for g in gaps) + "</ul>", unsafe_allow_html=True)
    else:
        st.markdown("<p>暂无</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# 发展建议
st.markdown('<div class="section-title">🎯 发展建议</div>', unsafe_allow_html=True)

suggest_col1, suggest_col2 = st.columns(2)
with suggest_col1:
    st.markdown('<div class="assessment-card"><h4>🤝 招商补链建议</h4>', unsafe_allow_html=True)
    items = diagnosis.get("investment_suggestions", [])
    if items:
        st.markdown("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>", unsafe_allow_html=True)
    else:
        st.markdown("<p>暂无</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="assessment-card"><h4>🌱 企业梯度培育建议</h4>', unsafe_allow_html=True)
    items = diagnosis.get("cultivation_suggestions", [])
    if items:
        st.markdown("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>", unsafe_allow_html=True)
    else:
        st.markdown("<p>暂无</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with suggest_col2:
    st.markdown('<div class="assessment-card"><h4>📜 政策培育建议</h4>', unsafe_allow_html=True)
    items = diagnosis.get("policy_suggestions", [])
    if items:
        st.markdown("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>", unsafe_allow_html=True)
    else:
        st.markdown("<p>暂无</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# 风险提醒
st.markdown('<div class="section-title">🚨 风险提醒</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="risk-card">
    {diagnosis.get("risk_warning", "暂无风险提醒")}
</div>
""", unsafe_allow_html=True)

st.info("💡 提示：诊断结论默认使用规则模板生成；配置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 后可启用 LLM 智能生成。")
