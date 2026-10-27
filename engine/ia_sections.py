"""
园区产业梳理 · 共享渲染模块
============================
「园区产业概况」单页共用的渲染逻辑：样式、工具函数、KPI 条、产业分类、
产业链图谱 + 优势/薄弱/缺失诊断卡、发展路径、招商目标、产业资源、报告导出。

五个步骤（填入材料 → 分类 → 链分析 → 建议 → 招商）在同一页面内经锚点定位，
分析结果经 st.session_state["industry_analysis_result"] 共享。
"""

import streamlit as st

from engine.industry_analyzer import to_markdown
from engine.industry_report_export import build_industry_word_report, build_industry_pdf_report

RESULT_KEY = "industry_analysis_result"


# ---------------------------------------------------------------- 基础工具

def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def analyze_material_quality(text: str) -> dict:
    """粗略检测材料结构：企业行数、含规模信息/资质信息的行数，用于给出补充建议"""
    import re
    out = {"enterprises": 0, "with_scale": 0, "with_qualification": 0}
    if not text:
        return out
    for line in text.splitlines():
        line = line.strip()
        if len(line) < 6:
            continue
        if not re.search(r"(公司|集团|工厂|研究院|研究所|中心|大学)", line):
            continue
        out["enterprises"] += 1
        if re.search(r"(亿元|万元|万人|员工|产值|营收|\d+\s*人)", line):
            out["with_scale"] += 1
        if re.search(r"(高新|专精特新|小巨人|上市)", line):
            out["with_qualification"] += 1
    return out


def get_result():
    """取当前分析结果；无结果渲染空状态引导并返回 None"""
    result = st.session_state.get(RESULT_KEY)
    if not result:
        st.markdown('<div class="ia-tip">尚未运行产业梳理。请先在'
                    '<a href="园区产业概况">🏭 园区产业概况</a> 填入基本信息并运行梳理，'
                    '本页内容将自动生成。</div>', unsafe_allow_html=True)
    return result


# ---------------------------------------------------------------- 样式

def inject_ia_css() -> None:
    st.markdown("""
<style>
:root {
    --td-brand: #0052D9; --td-brand-light: #E8F0FE;
    --td-success: #00A870; --td-warning: #ED7B2F; --td-danger: #D54941;
    --td-text: #1B2733; --td-muted: #6B7A8D; --td-border: #E3E8EF; --td-bg: #F5F7FA;
}
.ia-page-header { display: flex; align-items: flex-start; justify-content: space-between;
    gap: 1rem; margin-bottom: 0.25rem; }
.ia-title { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; }
.ia-subtitle { color: var(--td-muted); font-size: 0.92rem; margin-top: 0.25rem; line-height: 1.6; }
.ia-mode-badge { display: inline-flex; align-items: center; gap: 0.35rem;
    padding: 0.3rem 0.85rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600;
    white-space: nowrap; }
.ia-mode-llm { background: #E6F7F0; color: var(--td-success); border: 1px solid #BDE8D4; }
.ia-mode-tpl { background: #FFF4E8; color: var(--td-warning); border: 1px solid #FAD8B4; }

.ia-card { background: #fff; border: 1px solid var(--td-border); border-radius: 14px;
    padding: 1.35rem 1.5rem; box-shadow: 0 1px 3px rgba(27, 39, 51, 0.04); }
.ia-card-title { font-size: 1.02rem; font-weight: 700; margin-bottom: 0.15rem; }
.ia-card-desc { font-size: 0.83rem; color: var(--td-muted); margin-bottom: 0.9rem; }

/* KPI 条 */
.ia-kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.9rem; margin-bottom: 1.25rem; }
.ia-kpi { background: #fff; border: 1px solid var(--td-border); border-radius: 12px;
    padding: 1rem 1.15rem; display: flex; align-items: center; gap: 0.8rem; }
.ia-kpi-icon { width: 40px; height: 40px; border-radius: 10px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
.ia-kpi-value { font-size: 1.55rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; }
.ia-kpi-label { font-size: 0.78rem; color: var(--td-muted); }
.ia-kpi-trend { font-size: 0.72rem; color: #00875A; margin-top: 0.1rem; }

/* 产业链图谱 */
.ia-chain { margin: 0.5rem 0 0.25rem; }
.ia-chain-row { display: flex; align-items: stretch; gap: 0.75rem; margin-bottom: 0.75rem; }
.ia-chain-layer { flex: 0 0 92px; border-radius: 10px; display: flex; flex-direction: column;
    align-items: center; justify-content: center; padding: 0.6rem 0.4rem; gap: 0.15rem; }
.ia-chain-layer .layer-name { font-size: 0.92rem; font-weight: 700; }
.ia-chain-layer .layer-count { font-size: 0.72rem; opacity: 0.85; }
.ia-layer-up { background: #E6F7F0; color: #00875A; }
.ia-layer-mid { background: var(--td-brand-light); color: var(--td-brand); }
.ia-layer-down { background: #FFF4E8; color: #D2661A; }
.ia-chain-segs { flex: 1; display: flex; flex-wrap: wrap; gap: 0.55rem; align-content: flex-start; }
.ia-seg-chip { border: 1px solid var(--td-border); border-radius: 10px; padding: 0.5rem 0.8rem;
    background: #fff; font-size: 0.84rem; line-height: 1.4; }
.ia-seg-chip .seg-name { font-weight: 600; }
.ia-seg-chip .seg-count { display: inline-block; margin-left: 0.4rem; padding: 0 0.45rem;
    border-radius: 999px; font-size: 0.72rem; font-weight: 600; background: var(--td-bg);
    color: var(--td-muted); }
.ia-seg-chip .seg-ents { display: block; font-size: 0.76rem; color: var(--td-muted); margin-top: 0.15rem; }
.ia-seg-empty { border: 1.5px dashed var(--td-danger); border-radius: 10px; padding: 0.5rem 0.8rem;
    background: #FEF3F2; color: var(--td-danger); font-size: 0.84rem; font-weight: 600;
    display: flex; align-items: center; gap: 0.35rem; }
.ia-chain-arrow { text-align: center; color: var(--td-muted); font-size: 1rem;
    margin: -0.15rem 0 0.55rem 92px; }

/* 优势/薄弱/缺失 三诊断卡（仿「风险提示」卡片：左侧色条 + 徽标） */
.ia-gap-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.9rem; margin-top: 1rem; }
.ia-gap-card { background: #fff; border: 1px solid var(--td-border); border-radius: 12px;
    padding: 1rem 1.15rem; border-left: 4px solid var(--td-border); }
.ia-gap-card.gap-strong { border-left-color: #00A870; }
.ia-gap-card.gap-weak { border-left-color: #ED7B2F; }
.ia-gap-card.gap-empty { border-left-color: #D54941; }
.ia-gap-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.6rem; }
.ia-gap-title { font-size: 0.95rem; font-weight: 700; }
.ia-gap-badge { font-size: 0.72rem; font-weight: 600; padding: 0.12rem 0.55rem; border-radius: 999px; }
.ia-gap-card.gap-strong .ia-gap-badge { background: #E6F7F0; color: #00875A; }
.ia-gap-card.gap-weak .ia-gap-badge { background: #FFF4E8; color: #D2661A; }
.ia-gap-card.gap-empty .ia-gap-badge { background: #FEF3F2; color: #D54941; }
.ia-gap-item { font-size: 0.84rem; line-height: 1.7; color: var(--td-text); }
.ia-gap-item .gi-seg { font-weight: 600; }
.ia-gap-item .gi-ents { color: var(--td-muted); font-size: 0.78rem; }
.ia-gap-none { font-size: 0.82rem; color: var(--td-muted); }

/* 路径卡片 */
.ia-path-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.9rem; }
.ia-path-card { border-radius: 12px; border: 1px solid var(--td-border); background: #fff;
    padding: 1.1rem 1.2rem; }
.ia-path-head { display: flex; align-items: center; gap: 0.55rem; margin-bottom: 0.75rem; }
.ia-path-icon { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center;
    justify-content: center; font-size: 1.05rem; }
.ia-path-title { font-size: 0.98rem; font-weight: 700; }
.ia-path-sub { font-size: 0.75rem; color: var(--td-muted); }
.ia-path-item { border-top: 1px dashed var(--td-border); padding: 0.6rem 0 0.15rem; margin-top: 0.6rem; }
.ia-path-item .pi-head { font-size: 0.86rem; font-weight: 600; }
.ia-path-item .pi-action { font-size: 0.83rem; color: var(--td-text); margin-top: 0.2rem; line-height: 1.55; }
.ia-path-item .pi-why { font-size: 0.77rem; color: var(--td-muted); margin-top: 0.15rem; }

/* 资源卡 */
.ia-res-item { display: flex; gap: 0.6rem; padding: 0.6rem 0; border-top: 1px dashed var(--td-border); }
.ia-res-item:first-of-type { border-top: none; }
.ia-res-item .ri-icon { flex-shrink: 0; }
.ia-res-item .ri-name { font-size: 0.88rem; font-weight: 600; }
.ia-res-item .ri-meta { font-size: 0.78rem; color: var(--td-muted); margin-top: 0.1rem; line-height: 1.5; }

/* 章节头 */
.ia-section { display: flex; align-items: baseline; gap: 0.6rem; margin: 1.75rem 0 0.85rem; }
.ia-section-num { font-size: 0.78rem; font-weight: 700; color: #fff; background: var(--td-brand);
    border-radius: 6px; padding: 0.12rem 0.5rem; }
.ia-section-title { font-size: 1.12rem; font-weight: 700; }
.ia-section-note { font-size: 0.8rem; color: var(--td-muted); }

.ia-alert { display: flex; gap: 0.5rem; align-items: flex-start; background: #FEF3F2;
    border: 1px solid #F5C6C2; color: #B33B33; border-radius: 10px; padding: 0.7rem 1rem;
    font-size: 0.84rem; line-height: 1.55; margin-bottom: 0.8rem; }
.ia-tip { display: flex; gap: 0.5rem; align-items: flex-start; background: var(--td-bg);
    border: 1px solid var(--td-border); color: var(--td-muted); border-radius: 10px;
    padding: 0.7rem 1rem; font-size: 0.84rem; line-height: 1.55; margin-bottom: 0.8rem; }

/* 招商目标企业卡片 */
.ia-tcard { background: #fff; border: 1px solid var(--td-border); border-radius: 12px;
    padding: 0.95rem 1.1rem; margin-bottom: 0.7rem; box-shadow: 0 1px 3px rgba(27,39,51,0.04); }
.ia-tcard .tc-head { display: flex; align-items: center; justify-content: space-between;
    gap: 0.6rem; margin-bottom: 0.5rem; }
.ia-tcard .tc-name { font-size: 0.98rem; font-weight: 700; color: var(--td-text); }
.ia-tcard .tc-badge { flex-shrink: 0; font-size: 0.72rem; font-weight: 600;
    padding: 0.14rem 0.6rem; border-radius: 999px; }
.ia-tcard .tc-badge.kb { background: #E6F7F0; color: #00875A; border: 1px solid #BDE8D4; }
.ia-tcard .tc-badge.ai { background: #FFF4E8; color: #D2661A; border: 1px solid #FAD8B4; }
.ia-tcard .tc-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.55rem; }
.ia-tcard .tc-tag { font-size: 0.74rem; font-weight: 600; padding: 0.12rem 0.55rem;
    border-radius: 6px; background: var(--td-brand-light); color: var(--td-brand); }
.ia-tcard .tc-tag.loc { background: var(--td-bg); color: var(--td-muted); font-weight: 500; }
.ia-tcard .tc-line { font-size: 0.83rem; line-height: 1.55; color: var(--td-text); margin-top: 0.3rem; }
.ia-tcard .tc-k { display: inline-block; font-size: 0.72rem; font-weight: 600;
    color: var(--td-muted); background: var(--td-bg); border-radius: 5px;
    padding: 0.05rem 0.45rem; margin-right: 0.4rem; }

/* 同页步骤条（锚点导航，不跳新页面） */
.ia-steps { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem;
    margin: 0.9rem 0 1.1rem; }
.ia-steps a { display: inline-block; padding: 0.4rem 0.95rem; border-radius: 999px;
    background: #fff; border: 1px solid var(--td-border); color: var(--td-text);
    font-size: 0.84rem; font-weight: 600; text-decoration: none; transition: all .2s ease; }
.ia-steps a:hover { border-color: var(--td-brand); color: var(--td-brand);
    background: var(--td-brand-light); }
.ia-steps-sep { color: var(--td-muted); font-size: 0.8rem; }

@media (max-width: 900px) {
    .ia-kpi-grid, .ia-gap-grid { grid-template-columns: repeat(2, 1fr); }
    .ia-path-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


def render_ia_header(title: str, subtitle: str, result=None) -> None:
    mode_llm = bool(result and result.get("mode") == "llm" and not result.get("llm_error"))
    badge_cls = "ia-mode-llm" if mode_llm else "ia-mode-tpl"
    badge_txt = ("🔒 本地模式 · 材料不出本机" if result and result.get("local_only")
                 else ("🟢 智能模式" if mode_llm else "⚪ 本地模式"))
    st.markdown(f"""
    <div class="ia-page-header">
        <div>
            <div class="ia-title">{esc(title)}</div>
            <div class="ia-subtitle">{esc(subtitle)}</div>
        </div>
        <div class="ia-mode-badge {badge_cls}">{badge_txt}</div>
    </div>
    """, unsafe_allow_html=True)
    if result and result.get("llm_error"):
        st.warning(f"⚠️ 智能模式本次调用失败，已改用本地引擎生成：{result['llm_error']}")


# ---------------------------------------------------------------- 内部渲染件

def _render_chain_map(chain_map, gaps):
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


def _render_path_cards(paths):
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


def _render_target_cards(targets):
    """招商目标企业：企查查式卡片两列网格"""
    for i in range(0, len(targets), 2):
        cols = st.columns(2)
        for col, t in zip(cols, targets[i:i + 2]):
            is_kb = t.get("source") == "知识库"
            badge = ('<span class="tc-badge kb">🟢 知识库·已核实</span>' if is_kb
                     else '<span class="tc-badge ai">🟠 AI生成·待核实</span>')
            tags = [f'<span class="tc-tag">{esc(t.get("segment", ""))}</span>']
            if t.get("region"):
                tags.append(f'<span class="tc-tag loc">📍 {esc(t["region"])}</span>')
            lines = []
            if t.get("reason"):
                lines.append(f'<div class="tc-line"><span class="tc-k">配套逻辑</span>{esc(t["reason"])}</div>')
            if t.get("signal"):
                lines.append(f'<div class="tc-line"><span class="tc-k">落地线索</span>{esc(t["signal"])}</div>')
            with col:
                st.markdown(
                    f'<div class="ia-tcard"><div class="tc-head">'
                    f'<span class="tc-name">{esc(t.get("name", ""))}</span>{badge}</div>'
                    f'<div class="tc-tags">{"".join(tags)}</div>{"".join(lines)}</div>',
                    unsafe_allow_html=True)


# ---------------------------------------------------------------- 结果区块（模块页直接调用）

def _counts(result):
    all_ents = [e for g in result["classification"].get("industries", [])
                for e in g.get("enterprises", [])]
    segments = result["chain_map"].get("segments", [])
    gaps = result.get("gaps", {})
    return all_ents, segments, gaps


def render_kpi_strip(result) -> None:
    """核心指标条：识别企业 / 覆盖环节 / 薄弱环节 / 缺失环节"""
    all_ents, segments, gaps = _counts(result)
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


def render_classification(result) -> None:
    """产业分类：按产业方向分组，组内企业表格"""
    st.markdown('<div class="ia-section"><span class="ia-section-num">一</span>'
                '<span class="ia-section-title">产业分类</span>'
                '<span class="ia-section-note">企业逐一归类</span></div>',
                unsafe_allow_html=True)
    for group in result["classification"].get("industries", []):
        ents = group.get("enterprises", [])
        with st.expander(f"**{group['industry']}** · {len(ents)} 家企业", expanded=False):
            rows = [{"企业名称": e.get("name", ""), "主要产品": e.get("products", ""),
                     "核心技术": e.get("tech", ""), "规模": e.get("scale", "")} for e in ents]
            st.dataframe(rows, use_container_width=True, hide_index=True)


def render_gap_cards(result) -> None:
    """优势 / 薄弱 / 缺失 三诊断卡（仿决策系统的「风险提示」卡片）"""
    _, segments, gaps = _counts(result)
    strong = [s for s in segments if len(s.get("enterprises", [])) >= 2]
    weak = [s for s in segments if len(s.get("enterprises", [])) == 1]
    empty = [s for s in segments if not s.get("enterprises")]
    cards = [
        ("gap-strong", "✅ 优势环节", f"{len(strong)} 个", strong,
         "已有多家企业布局，具备配套基础"),
        ("gap-weak", "⚠️ 薄弱环节", f"{len(weak)} 个", weak,
         "仅单一企业，抗风险与议价能力弱"),
        ("gap-empty", "⛔ 缺失环节", f"{len(empty)} 个", empty,
         "链条断点，建议列入招商补链目标"),
    ]
    cols = st.columns(3)
    for col, (cls, title, badge, segs, note) in zip(cols, cards):
        items = "".join(
            f'<div class="ia-gap-item"><span class="gi-seg">{esc(s.get("segment", ""))}</span>'
            f'<span class="gi-ents">（{len(s.get("enterprises", []))} 家：'
            f'{"、".join(esc(n) for n in s.get("enterprises", [])[:3])}）</span></div>'
            for s in segs[:6])
        if not segs:
            items = '<div class="ia-gap-none">无</div>'
        with col:
            st.markdown(
                f'<div class="ia-gap-card {cls}"><div class="ia-gap-head">'
                f'<span class="ia-gap-title">{title}</span>'
                f'<span class="ia-gap-badge">{badge}</span></div>{items}'
                f'<div class="ia-gap-none" style="margin-top:0.5rem">{note}</div></div>',
                unsafe_allow_html=True)


def render_chain_analysis(result) -> None:
    """产业链分析：上中下游图谱 + 优势/薄弱/缺失诊断卡"""
    _, _, gaps = _counts(result)
    st.markdown('<div class="ia-section"><span class="ia-section-num">二</span>'
                '<span class="ia-section-title">产业链上下游分析</span>'
                '<span class="ia-section-note">上中下游环节分布 · 缺失环节已标红</span></div>',
                unsafe_allow_html=True)
    if gaps.get("is_template"):
        st.markdown('<div class="ia-tip">本地模式按关键词归位，环节较粗；智能模式下输出细化环节（如"正极材料""电芯"级）并判定真实缺失环节。</div>',
                    unsafe_allow_html=True)
    _render_chain_map(result["chain_map"], gaps)
    render_gap_cards(result)


def render_paths_section(result) -> None:
    """产业发展建议：强链/补链/延链"""
    st.markdown('<div class="ia-section"><span class="ia-section-num">三</span>'
                '<span class="ia-section-title">产业发展建议</span>'
                '<span class="ia-section-note">强链 · 补链 · 延链</span></div>',
                unsafe_allow_html=True)
    _render_path_cards(result.get("paths", {}))


def render_targets_section(result) -> None:
    """产业招商推荐：目标企业清单"""
    st.markdown('<div class="ia-section"><span class="ia-section-num">四</span>'
                '<span class="ia-section-title">产业招商推荐</span>'
                '<span class="ia-section-note">按缺失与薄弱环节定向招引</span></div>',
                unsafe_allow_html=True)
    if result.get("targets"):
        n_kb = sum(1 for t in result["targets"] if t.get("source") == "知识库")
        n_ai = len(result["targets"]) - n_kb
        st.markdown('<div class="ia-alert">🟢 <b>知识库条目</b>：人工整理、已核实，对接前建议复核最新动态；'
                    '🟠 <b>AI 生成条目</b>：基于公开信息生成，企业名称、所在地与落地线索请在正式对接前逐一人工核实。</div>',
                    unsafe_allow_html=True)
        _render_target_cards(result["targets"])
        st.caption(f"共 {len(result['targets'])} 家目标企业：知识库已核实 {n_kb} 家"
                   + (f"，AI 生成待核实 {n_ai} 家" if n_ai else ""))
    else:
        st.markdown('<div class="ia-tip">本次未生成招商目标清单。可在 <code>data/invest_targets.json</code> 中'
                    '维护已核实目标企业（按「产业 → 环节 → 企业」），或启用智能模式由 AI 自动补全。</div>',
                    unsafe_allow_html=True)


def render_resources_subsection(result) -> None:
    """研究院 / 协会资源（招商推荐的配套对接线索）"""
    res = result.get("resources", {})
    if not res:
        st.markdown('<div class="ia-tip">未命中本地产业资源知识库。可在 <code>data/industry_resources.json</code> 中按产业维护'
                    '已核实的研究院、协会与联盟，或启用智能模式由 AI 自动梳理该产业有影响力的机构。</div>',
                    unsafe_allow_html=True)
        return
    st.markdown('<div style="font-size:0.95rem;font-weight:700;margin:1.1rem 0 0.6rem">'
                '🏛️ 配套资源：研究院 / 协会</div>', unsafe_allow_html=True)
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


def render_export_block(result) -> None:
    """导出完整梳理报告：Markdown / Word / PDF"""
    st.divider()
    st.markdown('<div class="ia-section"><span class="ia-section-title">导出完整梳理报告</span>'
                '<span class="ia-section-note">Markdown / Word / PDF 三种格式</span></div>',
                unsafe_allow_html=True)
    md_bytes = to_markdown(result).encode("utf-8")
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
