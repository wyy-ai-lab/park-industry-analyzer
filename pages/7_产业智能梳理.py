"""
产业智能梳理
============
面向园区的"材料 → 洞察"入口：粘贴企业目录或文字材料，
智能体自动完成产业分类 → 上中下游环节梳理 → 强弱缺失分析
→ 强链补链延链路径 → 招商目标企业清单 → 研究院/协会资源。

界面风格参考腾讯云 / TDesign：流程步骤条、卡片化输入区、
横向产业链图谱、KPI 摘要条、分层结果呈现。

配置 ANTHROPIC_API_KEY / OPENAI_API_KEY 后为 LLM 全链路；
无 Key 时自动降级为模板模式（基础归位，目标企业与资源待 LLM 生成）。
"""

import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.industry_analyzer import run_industry_analysis, to_markdown
from engine.industry_report_export import build_industry_word_report, build_industry_pdf_report

inject_apple_theme()

# 示例材料：锂电新材料园区企业目录（演示模板模式/供 LLM 模式试用）
EXAMPLE_MATERIAL = """园区企业目录（示例 · 锂电新材料方向）
1. 安徽金泉新材料有限公司——主营正极材料前驱体，年产值约8亿元
2. 合肥硅源纳米科技有限公司——硅碳负极材料研发与生产
3. 皖江电解液科技有限公司——动力电池电解液及添加剂
4. 安徽蓝科隔膜材料有限公司——湿法隔膜基膜
5. 合肥星恒电芯制造有限公司——磷酸铁锂电芯
6. 安徽聚能电池系统有限公司——电池Pack集成
7. 合肥精测仪器股份有限公司——电池检测设备
8. 皖江智能装备有限公司——材料生产线设备
9. 安徽循环再生科技有限公司——退役电池回收梯次利用
10. 合肥新能物流有限公司——危化品仓储与运输
"""

# ---------------------------------------------------------------- 页面级 CSS
st.markdown("""
<style>
/* ===== TDesign 风格设计令牌 ===== */
:root {
    --td-brand: #0052D9;
    --td-brand-light: #E8F0FE;
    --td-success: #00A870;
    --td-warning: #ED7B2F;
    --td-danger: #D54941;
    --td-text: #1B2733;
    --td-muted: #6B7A8D;
    --td-border: #E3E8EF;
    --td-bg: #F5F7FA;
}

/* ===== 标题区 ===== */
.ia-page-header {
    display: flex; align-items: flex-start; justify-content: space-between;
    gap: 1rem; margin-bottom: 0.25rem;
}
.ia-title { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; }
.ia-subtitle { color: var(--td-muted); font-size: 0.92rem; margin-top: 0.25rem; line-height: 1.6; }
.ia-mode-badge {
    display: inline-flex; align-items: center; gap: 0.35rem;
    padding: 0.3rem 0.85rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600;
    white-space: nowrap;
}
.ia-mode-llm { background: #E6F7F0; color: var(--td-success); border: 1px solid #BDE8D4; }
.ia-mode-tpl { background: #FFF4E8; color: var(--td-warning); border: 1px solid #FAD8B4; }

/* ===== 流程步骤条 ===== */
.ia-stepbar {
    display: flex; align-items: center; gap: 0;
    background: var(--td-bg); border: 1px solid var(--td-border);
    border-radius: 12px; padding: 0.85rem 1.25rem; margin: 1.25rem 0 1.5rem;
    overflow-x: auto;
}
.ia-step { display: flex; align-items: center; gap: 0.5rem; flex-shrink: 0; }
.ia-step-num {
    width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.78rem; font-weight: 700;
    background: #fff; color: var(--td-muted); border: 1.5px solid var(--td-border);
}
.ia-step-label { font-size: 0.84rem; color: var(--td-muted); font-weight: 500; white-space: nowrap; }
.ia-step.done .ia-step-num { background: var(--td-brand); border-color: var(--td-brand); color: #fff; }
.ia-step.done .ia-step-label { color: var(--td-text); font-weight: 600; }
.ia-step.current .ia-step-num {
    background: #fff; border-color: var(--td-brand); color: var(--td-brand);
    box-shadow: 0 0 0 3px rgba(0, 82, 217, 0.15);
}
.ia-step.current .ia-step-label { color: var(--td-brand); font-weight: 600; }
.ia-step-line {
    flex: 1 1 18px; min-width: 14px; height: 1.5px; background: var(--td-border); margin: 0 0.5rem;
}
.ia-step-line.done { background: var(--td-brand); }

/* ===== 卡片通用 ===== */
.ia-card {
    background: #fff; border: 1px solid var(--td-border); border-radius: 14px;
    padding: 1.35rem 1.5rem; box-shadow: 0 1px 3px rgba(27, 39, 51, 0.04);
}
.ia-card-title { font-size: 1.02rem; font-weight: 700; margin-bottom: 0.15rem; }
.ia-card-desc { font-size: 0.83rem; color: var(--td-muted); margin-bottom: 0.9rem; }

/* ===== KPI 条 ===== */
.ia-kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.9rem; margin-bottom: 1.25rem; }
.ia-kpi {
    background: #fff; border: 1px solid var(--td-border); border-radius: 12px;
    padding: 1rem 1.15rem; display: flex; align-items: center; gap: 0.8rem;
}
.ia-kpi-icon {
    width: 40px; height: 40px; border-radius: 10px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center; font-size: 1.2rem;
}
.ia-kpi-value { font-size: 1.55rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; }
.ia-kpi-label { font-size: 0.78rem; color: var(--td-muted); }

/* ===== 产业链图谱 ===== */
.ia-chain { margin: 0.5rem 0 0.25rem; }
.ia-chain-row { display: flex; align-items: stretch; gap: 0.75rem; margin-bottom: 0.75rem; }
.ia-chain-layer {
    flex: 0 0 92px; border-radius: 10px; display: flex; flex-direction: column;
    align-items: center; justify-content: center; padding: 0.6rem 0.4rem; gap: 0.15rem;
}
.ia-chain-layer .layer-name { font-size: 0.92rem; font-weight: 700; }
.ia-chain-layer .layer-count { font-size: 0.72rem; opacity: 0.85; }
.ia-layer-up { background: #E6F7F0; color: #00875A; }
.ia-layer-mid { background: var(--td-brand-light); color: var(--td-brand); }
.ia-layer-down { background: #FFF4E8; color: #D2661A; }
.ia-chain-segs { flex: 1; display: flex; flex-wrap: wrap; gap: 0.55rem; align-content: flex-start; }
.ia-seg-chip {
    border: 1px solid var(--td-border); border-radius: 10px; padding: 0.5rem 0.8rem;
    background: #fff; font-size: 0.84rem; line-height: 1.4;
}
.ia-seg-chip .seg-name { font-weight: 600; }
.ia-seg-chip .seg-count {
    display: inline-block; margin-left: 0.4rem; padding: 0 0.45rem; border-radius: 999px;
    font-size: 0.72rem; font-weight: 600; background: var(--td-bg); color: var(--td-muted);
}
.ia-seg-chip .seg-ents { display: block; font-size: 0.76rem; color: var(--td-muted); margin-top: 0.15rem; }
.ia-seg-empty {
    border: 1.5px dashed var(--td-danger); border-radius: 10px; padding: 0.5rem 0.8rem;
    background: #FEF3F2; color: var(--td-danger); font-size: 0.84rem; font-weight: 600;
    display: flex; align-items: center; gap: 0.35rem;
}
.ia-chain-arrow { text-align: center; color: var(--td-muted); font-size: 1rem; margin: -0.15rem 0 0.55rem 92px; }

/* ===== 路径卡片 ===== */
.ia-path-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.9rem; }
.ia-path-card { border-radius: 12px; border: 1px solid var(--td-border); background: #fff; padding: 1.1rem 1.2rem; }
.ia-path-head { display: flex; align-items: center; gap: 0.55rem; margin-bottom: 0.75rem; }
.ia-path-icon { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; }
.ia-path-title { font-size: 0.98rem; font-weight: 700; }
.ia-path-sub { font-size: 0.75rem; color: var(--td-muted); }
.ia-path-item { border-top: 1px dashed var(--td-border); padding: 0.6rem 0 0.15rem; margin-top: 0.6rem; }
.ia-path-item .pi-head { font-size: 0.86rem; font-weight: 600; }
.ia-path-item .pi-action { font-size: 0.83rem; color: var(--td-text); margin-top: 0.2rem; line-height: 1.55; }
.ia-path-item .pi-why { font-size: 0.77rem; color: var(--td-muted); margin-top: 0.15rem; }

/* ===== 资源卡 ===== */
.ia-res-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.9rem; }
.ia-res-item { display: flex; gap: 0.6rem; padding: 0.6rem 0; border-top: 1px dashed var(--td-border); }
.ia-res-item:first-of-type { border-top: none; }
.ia-res-item .ri-icon { flex-shrink: 0; }
.ia-res-item .ri-name { font-size: 0.88rem; font-weight: 600; }
.ia-res-item .ri-meta { font-size: 0.78rem; color: var(--td-muted); margin-top: 0.1rem; line-height: 1.5; }

/* ===== 章节头 ===== */
.ia-section {
    display: flex; align-items: baseline; gap: 0.6rem;
    margin: 1.75rem 0 0.85rem;
}
.ia-section-num {
    font-size: 0.78rem; font-weight: 700; color: #fff; background: var(--td-brand);
    border-radius: 6px; padding: 0.12rem 0.5rem;
}
.ia-section-title { font-size: 1.12rem; font-weight: 700; }
.ia-section-note { font-size: 0.8rem; color: var(--td-muted); }

/* ===== 核实标签 ===== */
.ia-verify-tag {
    display: inline-flex; align-items: center; padding: 0.15rem 0.6rem; border-radius: 999px;
    font-size: 0.75rem; font-weight: 600; background: #FFF4E8; color: var(--td-warning);
    border: 1px solid #FAD8B4;
}
.ia-alert {
    display: flex; gap: 0.5rem; align-items: flex-start;
    background: #FEF3F2; border: 1px solid #F5C6C2; color: #B33B33;
    border-radius: 10px; padding: 0.7rem 1rem; font-size: 0.84rem; line-height: 1.55; margin-bottom: 0.8rem;
}
.ia-tip {
    display: flex; gap: 0.5rem; align-items: flex-start;
    background: var(--td-bg); border: 1px solid var(--td-border); color: var(--td-muted);
    border-radius: 10px; padding: 0.7rem 1rem; font-size: 0.84rem; line-height: 1.55; margin-bottom: 0.8rem;
}

@media (max-width: 900px) {
    .ia-kpi-grid { grid-template-columns: repeat(2, 1fr); }
    .ia-path-grid, .ia-res-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- 工具函数

def render_stepbar(current: int):
    """渲染六阶段流程步骤条；current 为当前进行到的阶段（1-6，0 表示未开始）"""
    steps = [("①", "提供材料"), ("②", "产业分类"), ("③", "环节梳理"),
             ("④", "优化路径"), ("⑤", "招商清单"), ("⑥", "产业资源")]
    parts = ['<div class="ia-stepbar">']
    for i, (num, label) in enumerate(steps, start=1):
        state = "done" if (current == 7 or i < current) else "current" if i == current else ""
        icon = "✓" if (current == 7 or i < current) else num
        parts.append(
            f'<div class="ia-step {state}">'
            f'<div class="ia-step-num">{icon}</div>'
            f'<div class="ia-step-label">{label}</div></div>'
        )
        if i < len(steps):
            line_done = "done" if (current == 7 or i < current) else ""
            parts.append(f'<div class="ia-step-line {line_done}"></div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_chain_map(chain_map, gaps):
    """横向产业链图谱：上游→中游→下游，环节卡片化，缺失红色虚线"""
    layer_cfg = [("上游", "ia-layer-up", "🌾"), ("中游", "ia-layer-mid", "⚙️"), ("下游", "ia-layer-down", "🚀")]
    segments = chain_map.get("segments", [])
    html = ['<div class="ia-chain">']
    for idx, (layer, cls, icon) in enumerate(layer_cfg):
        segs = [s for s in segments if s.get("layer") == layer]
        n_ents = sum(len(s.get("enterprises", [])) for s in segs)
        html.append('<div class="ia-chain-row">')
        html.append(
            f'<div class="ia-chain-layer {cls}"><div style="font-size:1.1rem">{icon}</div>'
            f'<div class="layer-name">{layer}</div>'
            f'<div class="layer-count">{n_ents} 家企业</div></div>'
        )
        html.append('<div class="ia-chain-segs">')
        if not segs:
            html.append('<div class="ia-seg-empty">⚠️ 该层级尚无企业布局</div>')
        for s in segs:
            ents = s.get("enterprises", [])
            if ents:
                names = "、".join(esc(n) for n in ents[:4]) + (" 等" if len(ents) > 4 else "")
                html.append(
                    f'<div class="ia-seg-chip"><span class="seg-name">{esc(s["segment"])}</span>'
                    f'<span class="seg-count">{len(ents)} 家</span>'
                    f'<span class="seg-ents">{names}</span></div>'
                )
            else:
                html.append(f'<div class="ia-seg-empty">＋ {esc(s["segment"])}（缺失）</div>')
        html.append("</div></div>")
        if idx < 2:
            arrow = "▼ 向下游延伸" if idx == 0 else "▼ 向应用与服务延伸"
            html.append(f'<div class="ia-chain-arrow">{arrow}</div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_path_cards(paths):
    """强链/补链/延链三卡片"""
    cfg = [
        ("strengthen", "🔧", "强链", "巩固优势 · 做大规模", "#E8F0FE", "#0052D9"),
        ("complete", "🧩", "补链", "招引缺失 · 补齐断点", "#E6F7F0", "#00875A"),
        ("extend", "➡️", "延链", "高附加值 · 双向延伸", "#FFF4E8", "#D2661A"),
    ]
    cols = st.columns(3)
    for col, (key, icon, title, sub, bg, fg) in zip(cols, cfg):
        items = paths.get(key, [])
        body = [f'<div class="ia-path-card"><div class="ia-path-head">'
                f'<div class="ia-path-icon" style="background:{bg};color:{fg}">{icon}</div>'
                f'<div><div class="ia-path-title">{title}</div>'
                f'<div class="ia-path-sub">{sub}</div></div></div>']
        if not items:
            body.append('<div class="ia-path-item"><div class="pi-action">暂无建议</div></div>')
        for it in items:
            head = esc(it.get("segment") or it.get("direction", ""))
            body.append(
                f'<div class="ia-path-item"><div class="pi-head">{head}</div>'
                f'<div class="pi-action">{esc(it.get("action", ""))}</div>'
                f'<div class="pi-why">依据:{esc(it.get("rationale", ""))}</div></div>'
            )
        body.append("</div>")
        with col:
            st.markdown("".join(body), unsafe_allow_html=True)


# ---------------------------------------------------------------- 标题区
result = st.session_state.get("industry_analysis_result")
current_stage = 7 if result else 1

st.markdown(f"""
<div class="ia-page-header">
    <div>
        <div class="ia-title">🧭 产业智能梳理</div>
        <div class="ia-subtitle">提供企业目录、园区介绍等基础材料，自动完成产业分类、上中下游分环节梳理、
        强弱缺失诊断与强链补链延链路径规划，并输出招商目标企业清单与研究院/协会资源。</div>
    </div>
    <div class="ia-mode-badge {'ia-mode-llm' if result and result.get('mode') == 'llm' else 'ia-mode-tpl'}">
        {'🟢 LLM 智能模式' if result and result.get('mode') == 'llm' else '🟡 模板模式 · 配置 API Key 解锁全链路'}
    </div>
</div>
""", unsafe_allow_html=True)

# 会话写入须在文本域等组件创建之前完成（Streamlit 禁止对已实例化组件的 key 赋值）：
# 用标志位 + rerun 的方式，在脚本最前置位应用填入内容
if st.session_state.pop("_fill_example", None):
    st.session_state["industry_material"] = EXAMPLE_MATERIAL
    st.session_state["_notice"] = "已填入示例材料，可直接点击「开始产业梳理」"
if st.session_state.pop("_fill_upload", None):
    st.session_state["industry_material"] = st.session_state.pop("_uploaded_text", "")
_notice = st.session_state.pop("_notice", None)
if _notice:
    st.success(_notice)

render_stepbar(current_stage)

# ---------------------------------------------------------------- 第一步：材料输入
input_col, opt_col = st.columns([3, 1], gap="large")

with input_col:
    st.markdown('<div class="ia-card">', unsafe_allow_html=True)
    tab_text, tab_file = st.tabs(["📝 粘贴文本", "📎 上传文件"])

    with tab_text:
        material = st.text_area(
            "企业目录 / 园区介绍 / 文字材料",
            height=210,
            key="industry_material",
            label_visibility="collapsed",
            placeholder="每行一家企业最佳（企业名——主营产品），也支持整段文字材料",
        )
    with tab_file:
        up = st.file_uploader("上传 .txt / .csv / .xlsx 文件", type=["txt", "csv", "xlsx"],
                              label_visibility="collapsed")
        if up is not None:
            try:
                if up.name.endswith(".txt"):
                    uploaded_text = up.read().decode("utf-8", errors="ignore")
                else:
                    import pandas as pd
                    df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
                    uploaded_text = df.to_string(index=False)
                # 组件已渲染，不能直写其 key：置标志位后 rerun，由脚本前置位统一填入
                st.session_state["_uploaded_text"] = uploaded_text
                st.session_state["_fill_upload"] = True
                st.session_state["_notice"] = f"已读取 {up.name}（{len(uploaded_text)} 字符），内容已填入左侧文本域"
                st.rerun()
            except Exception as e:
                st.error(f"文件读取失败:{e}")
                material = st.session_state.get("industry_material", "")
        else:
            material = st.session_state.get("industry_material", "")

    btn_col, tip_col = st.columns([1, 2])
    with btn_col:
        run_clicked = st.button("🚀 开始产业梳理", type="primary", use_container_width=True)
    with tip_col:
        if st.button("📋 填入示例材料", use_container_width=True):
            st.session_state["_fill_example"] = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with opt_col:
    st.markdown('<div class="ia-card">', unsafe_allow_html=True)
    st.markdown('<div class="ia-card-title">辅助信息</div>'
                '<div class="ia-card-desc">让分类与招商建议更贴合园区实际</div>',
                unsafe_allow_html=True)
    focus_hint = st.text_input("产业方向提示", placeholder="如：锂电新材料")
    region = st.text_input("目标招商区域", placeholder="如：长三角 / 不限")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="ia-card" style="margin-top:0.9rem">', unsafe_allow_html=True)
    st.markdown('<div class="ia-card-title">💡 这个页面能做什么</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.83rem;color:var(--td-muted);line-height:1.8">'
        "识别材料中的企业并归类产业方向<br>"
        "归位到上中下游具体环节<br>"
        "诊断薄弱与缺失环节<br>"
        "生成强链 / 补链 / 延链路径<br>"
        "输出招商目标企业清单¹<br>"
        "梳理研究院 / 协会资源¹<br>"
        '<span style="font-size:0.75rem;opacity:0.8">¹ 需配置 API Key</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- 运行分析
if run_clicked:
    if not (material or "").strip():
        st.warning("请先粘贴材料或上传文件")
    else:
        with st.status("正在进行产业梳理，请稍候…", expanded=True) as status:
            result = run_industry_analysis(material.strip(), focus_hint.strip(), region.strip())
            status.update(label="梳理完成", state="complete")
        st.session_state["industry_analysis_result"] = result
        st.rerun()

if not result:
    st.markdown('<div class="ia-tip">👆 提供材料后点击「开始产业梳理」。可点「📋 填入示例材料」快速体验完整流程。</div>',
                unsafe_allow_html=True)
    st.stop()

render_stepbar(7)

# ---------------------------------------------------------------- KPI 摘要
all_ents = [e for g in result["classification"].get("industries", [])
            for e in g.get("enterprises", [])]
segments = result["chain_map"].get("segments", [])
gaps = result.get("gaps", {})
n_weak = len(gaps.get("weak_segments", []))
n_empty = len(gaps.get("empty_segments", []))

st.markdown(f"""
<div class="ia-kpi-grid">
    <div class="ia-kpi"><div class="ia-kpi-icon" style="background:#E8F0FE">🏢</div>
        <div><div class="ia-kpi-value">{len(all_ents)}</div><div class="ia-kpi-label">识别企业</div></div></div>
    <div class="ia-kpi"><div class="ia-kpi-icon" style="background:#F0EBFA">🧩</div>
        <div><div class="ia-kpi-value">{len(segments)}</div><div class="ia-kpi-label">覆盖环节</div></div></div>
    <div class="ia-kpi"><div class="ia-kpi-icon" style="background:#FFF4E8">⚠️</div>
        <div><div class="ia-kpi-value" style="color:#D2661A">{n_weak}</div><div class="ia-kpi-label">薄弱环节</div></div></div>
    <div class="ia-kpi"><div class="ia-kpi-icon" style="background:#FEF3F2">⛔</div>
        <div><div class="ia-kpi-value" style="color:#D54941">{n_empty}</div><div class="ia-kpi-label">缺失环节</div></div></div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- ② 产业链图谱
st.markdown('<div class="ia-section"><span class="ia-section-num">②</span>'
            '<span class="ia-section-title">产业链图谱</span>'
            '<span class="ia-section-note">上中下游环节分布 · 缺失环节已标红</span></div>',
            unsafe_allow_html=True)
if gaps.get("is_template"):
    st.markdown('<div class="ia-tip">模板模式按关键词归位，环节较粗；配置 API Key 后输出细化环节（如"正极材料""电芯"级）并判定真实缺失环节。</div>',
                unsafe_allow_html=True)
render_chain_map(result["chain_map"], gaps)

# ---------------------------------------------------------------- ① 产业分类明细
st.markdown('<div class="ia-section"><span class="ia-section-num">①</span>'
            '<span class="ia-section-title">产业分类明细</span>'
            '<span class="ia-section-note">企业逐一归类</span></div>',
            unsafe_allow_html=True)
for group in result["classification"].get("industries", []):
    ents = group.get("enterprises", [])
    with st.expander(f"**{group['industry']}** · {len(ents)} 家企业", expanded=False):
        rows = [{"企业名称": e.get("name", ""), "主要产品": e.get("products", ""),
                 "核心技术": e.get("tech", ""), "规模": e.get("scale", "")} for e in ents]
        st.dataframe(rows, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------- ④ 优化路径
st.markdown('<div class="ia-section"><span class="ia-section-num">④</span>'
            '<span class="ia-section-title">强链 · 补链 · 延链路径</span>'
            '<span class="ia-section-note">基于强弱缺失诊断生成</span></div>',
            unsafe_allow_html=True)
render_path_cards(result.get("paths", {}))

# ---------------------------------------------------------------- ⑤ 招商目标清单
st.markdown('<div class="ia-section"><span class="ia-section-num">⑤</span>'
            '<span class="ia-section-title">招商目标企业清单</span>'
            f'<span class="ia-section-note">{"目标区域偏好：" + esc(result.get("region")) if result.get("region") else ""}</span></div>',
            unsafe_allow_html=True)
if result.get("targets"):
    n_kb = sum(1 for t in result["targets"] if t.get("source") == "知识库")
    n_ai = len(result["targets"]) - n_kb
    st.markdown('<div class="ia-alert">🟢 <b>知识库条目</b>：人工整理、已核实，对接前建议复核最新动态；'
                '🟠 <b>AI 生成条目</b>：基于公开信息生成，企业名称、所在地与落地线索请在正式对接前逐一人工核实。</div>',
                unsafe_allow_html=True)
    trows = [{"目标企业": t.get("name", ""), "对应环节": t.get("segment", ""),
              "所在地": t.get("region", ""), "配套逻辑": t.get("reason", ""),
              "落地线索": t.get("signal", ""),
              "来源": "🟢 知识库·已核实" if t.get("source") == "知识库" else "🟠 AI生成·待核实"}
             for t in result["targets"]]
    st.dataframe(trows, use_container_width=True, hide_index=True)
    st.caption(f"共 {len(result['targets'])} 家目标企业：知识库已核实 {n_kb} 家"
               + (f"，AI 生成待核实 {n_ai} 家" if n_ai else ""))
else:
    st.markdown('<div class="ia-tip">未命中本地招商知识库，且未配置 API Key。'
                '可在 <code>data/invest_targets.json</code> 中按「产业 → 环节 → 企业」维护已核实目标企业，'
                '或配置 ANTHROPIC_API_KEY / OPENAI_API_KEY 后由 AI 基于缺失与薄弱环节自动补全。</div>',
                unsafe_allow_html=True)

# ---------------------------------------------------------------- ⑥ 产业资源
st.markdown('<div class="ia-section"><span class="ia-section-num">⑥</span>'
            '<span class="ia-section-title">研究院 / 协会资源</span>'
            '<span class="ia-section-note">产学研与行业组织对接线索</span></div>',
            unsafe_allow_html=True)
res = result.get("resources", {})
if res:
    rc = st.columns(2)
    with rc[0]:
        st.markdown('<div class="ia-card"><div class="ia-card-title">🔬 研究机构</div>', unsafe_allow_html=True)
        for i in res.get("institutes", []):
            st.markdown(
                f'<div class="ia-res-item"><div class="ri-icon">🔬</div><div>'
                f'<div class="ri-name">{esc(i.get("name", ""))}'
                f'<span style="color:var(--td-muted);font-weight:400"> · {esc(i.get("location", ""))}</span></div>'
                f'<div class="ri-meta">{esc(i.get("focus", ""))}</div></div></div>',
                unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with rc[1]:
        st.markdown('<div class="ia-card"><div class="ia-card-title">🏛️ 行业组织</div>', unsafe_allow_html=True)
        for a in res.get("associations", []):
            st.markdown(
                f'<div class="ia-res-item"><div class="ri-icon">🏛️</div><div>'
                f'<div class="ri-name">{esc(a.get("name", ""))}</div>'
                f'<div class="ri-meta">{esc(a.get("focus", ""))}</div></div></div>',
                unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="ia-tip">未命中本地产业资源知识库。可在 <code>data/industry_resources.json</code> 中按产业维护'
                '已核实的研究院、协会与联盟，或配置 API Key 后由 AI 自动梳理该产业有影响力的机构。</div>',
                unsafe_allow_html=True)

# ---------------------------------------------------------------- 导出
st.divider()
st.markdown('<div class="ia-section"><span class="ia-section-title">导出完整梳理报告</span>'
            '<span class="ia-section-note">Markdown / Word / PDF 三种格式</span></div>',
            unsafe_allow_html=True)
md_report = to_markdown(result)
md_bytes = md_report.encode("utf-8")
docx_bytes = pdf_bytes = None
docx_err = pdf_err = None
try:
    docx_bytes = build_industry_word_report(result).getvalue()
except Exception as exc:  # noqa: BLE001
    docx_err = str(exc)
try:
    pdf_bytes = build_industry_pdf_report(result).getvalue()
except Exception as exc:  # noqa: BLE001
    pdf_err = str(exc)

export_cols = st.columns(3)
with export_cols[0]:
    st.download_button("📥 Markdown", data=md_bytes,
                       file_name="产业梳理报告.md", mime="text/markdown",
                       use_container_width=True)
with export_cols[1]:
    if docx_bytes:
        st.download_button("📥 Word", data=docx_bytes,
                           file_name="产业梳理报告.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           use_container_width=True)
    else:
        st.button("📥 Word（不可用）", disabled=True, use_container_width=True)
with export_cols[2]:
    if pdf_bytes:
        st.download_button("📥 PDF", data=pdf_bytes,
                           file_name="产业梳理报告.pdf", mime="application/pdf",
                           use_container_width=True)
    else:
        st.button("📥 PDF（不可用）", disabled=True, use_container_width=True)
for fmt, err in (("Word", docx_err), ("PDF", pdf_err)):
    if err:
        st.warning(f"{fmt} 导出失败：{err}")
