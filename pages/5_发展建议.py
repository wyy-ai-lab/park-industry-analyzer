import base64

import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.park_metrics import load_park_enterprises, compute_metrics
from engine.park_llm import generate_diagnosis
from engine.park_charts import (
    build_industry_pie_chart,
    build_chain_layer_chart,
    build_tier_pyramid_chart,
    build_segment_strength_chart,
    build_top_enterprises_bar,
    fig_to_image_bytes,
)
from engine.park_report_export import (
    build_park_markdown_report,
    build_park_word_report,
    build_park_pdf_report,
    build_park_html_report,
)

st.set_page_config(
    page_title="发展建议 - 政策-产业-企业智能体",
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
.export-btn {
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">💡 发展建议</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">基于园区产业数据生成结构化诊断结论与发展建议。</div>', unsafe_allow_html=True)

# 加载数据
data = load_park_enterprises()
if not data or not data.get("enterprises"):
    if st.session_state.get("use_demo_data", True):
        st.warning("⚠️ 未找到园区企业数据，请确认 `data/park_enterprises.json` 存在。")
    else:
        st.warning("📦 演示数据已关闭，当前为「未接入数据」状态。返回首页打开左侧开关「载入演示数据」即可查看演示内容。")
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

st.divider()

# 报告导出
st.markdown('<div class="section-title">📦 报告导出</div>', unsafe_allow_html=True)
st.markdown("<p style='color: var(--apple-muted); margin-bottom: 1rem;'>将诊断结论导出为 Markdown、Word、PDF 或 HTML 格式，便于汇报与分享。</p>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _generate_report_assets(park_name: str, metrics_json: str, diagnosis_json: str):
    """预生成图表与报告，避免每次交互重复渲染"""
    import json
    metrics = json.loads(metrics_json)
    diagnosis = json.loads(diagnosis_json)

    # 构建 segment_status 映射
    segment_strength = metrics.get("segment_strength", {})
    segment_status = {}
    for status, segments in segment_strength.items():
        status_label = {"strong": "强势", "weak": "薄弱", "missing": "缺失"}.get(status, "正常")
        for seg in segments:
            segment_status[seg] = status_label

    figs = {
        "industry_pie": build_industry_pie_chart(
            metrics.get("sub_industry_distribution", {}),
            height=440,
            annotation_text=f"产业链完整度 {metrics.get('completeness_score', 0)} 分",
        ),
        "chain_layer": build_chain_layer_chart(
            metrics.get("chain_distribution", {}),
            height=400,
        ),
        "tier_pyramid": build_tier_pyramid_chart(
            metrics.get("tier_distribution", {}),
            height=420,
        ),
        "segment_strength": build_segment_strength_chart(
            metrics.get("segment_distribution", {}),
            segment_status,
            height=520,
            annotation_text=f"本地配套率 {metrics.get('local_support_rate', 0)}%",
        ),
        "top_enterprises": build_top_enterprises_bar(
            metrics.get("top_enterprises", []),
            top_n=10,
            height=480,
        ),
    }

    charts_bytes = {}
    charts_base64 = {}
    try:
        for key, fig in figs.items():
            img_bytes = fig_to_image_bytes(fig, format="png", width=900, scale=2)
            charts_bytes[key] = img_bytes
            charts_base64[key] = base64.b64encode(img_bytes).decode("utf-8")
    except Exception as e:
        st.warning(f"图表导出失败（可能未正确安装 kaleido）：{e}")

    return metrics, diagnosis, charts_bytes, charts_base64


import json as _json
_metrics_json = _json.dumps(metrics, ensure_ascii=False, default=str)
_diagnosis_json = _json.dumps(diagnosis, ensure_ascii=False, default=str)
metrics_cached, diagnosis_cached, charts_bytes, charts_base64 = _generate_report_assets(
    metrics.get("park_name", "未知园区"), _metrics_json, _diagnosis_json
)

park_name = metrics_cached.get("park_name", "未知园区")
from datetime import datetime
date_suffix = datetime.now().strftime("%Y%m%d")

export_col1, export_col2, export_col3, export_col4 = st.columns(4)

with export_col1:
    md_content = build_park_markdown_report(metrics_cached, diagnosis_cached)
    st.download_button(
        label="📄 导出 Markdown",
        data=md_content,
        file_name=f"{park_name}_产业诊断报告_{date_suffix}.md",
        mime="text/markdown",
        use_container_width=True,
    )

with export_col2:
    try:
        word_buffer = build_park_word_report(metrics_cached, diagnosis_cached, charts_bytes)
        st.download_button(
            label="📝 导出 Word",
            data=word_buffer,
            file_name=f"{park_name}_产业诊断报告_{date_suffix}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Word 导出失败：{e}")

with export_col3:
    try:
        pdf_buffer = build_park_pdf_report(metrics_cached, diagnosis_cached, charts_bytes)
        st.download_button(
            label="📕 导出 PDF",
            data=pdf_buffer,
            file_name=f"{park_name}_产业诊断报告_{date_suffix}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"PDF 导出失败：{e}")

with export_col4:
    html_content = build_park_html_report(metrics_cached, diagnosis_cached, charts_base64)
    st.download_button(
        label="🌐 导出 HTML",
        data=html_content,
        file_name=f"{park_name}_产业诊断报告_{date_suffix}.html",
        mime="text/html",
        use_container_width=True,
    )

st.info("💡 提示：诊断结论默认使用规则模板生成；配置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 后可启用 LLM 智能生成。")
