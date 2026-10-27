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
from datetime import datetime

from engine.ui_helpers import inject_apple_theme
from engine.auth import require_auth
try:  # 兼容部署环境中尚未热更新的旧版 auth 模块（缺 get_app_mode 时降级为演示模式）
    from engine.auth import get_app_mode
except ImportError:
    def get_app_mode() -> str:
        return "demo"
from engine.industry_analyzer import run_industry_analysis, to_markdown
from engine.industry_report_export import build_industry_word_report, build_industry_pdf_report

inject_apple_theme()

require_auth()

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

# 企业清单模板（CSV，带 BOM 保证 Excel 打开不乱码）：用户照着填即可
TEMPLATE_CSV = (
    "企业名称,主营产品,年产值(亿元),员工数,资质,核心技术\n"
    "合肥星恒电芯制造有限公司,磷酸铁锂电芯,5.2,300,高新技术企业,磷酸铁锂快充工艺\n"
).encode("utf-8-sig")

MATERIAL_GUIDE = """
**🟢 最低可用** —— 每行一家企业：名称 + 主营产品
```
合肥星恒电芯制造有限公司——磷酸铁锂电芯
```
产出：产业分类、环节归位、强弱缺失诊断、优化路径。

**🟡 标准材料**（推荐）—— 加上规模与资质
在企业行中补充：年产值、员工数、资质（高企/专精特新/无）。
额外产出：链主识别、企业梯队分层、重点培育建议。

**🔵 最佳材料** —— 企业清单（Excel 最佳）+ 右侧「园区背景」
在「⚙️ 园区背景」中填写所在城市、园区级别、目标招商区域，
招商推荐将结合区位与园区定位生成，而不是泛泛列名单。
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


def render_target_cards(targets):
    """招商目标企业：企查查式卡片两列网格"""
    st.markdown("""
    <style>
    .ia-tcard { background:#fff; border:1px solid var(--td-border); border-radius:12px;
                padding:0.95rem 1.1rem; margin-bottom:0.7rem;
                box-shadow:0 1px 3px rgba(27,39,51,0.04); }
    .ia-tcard .tc-head { display:flex; align-items:center; justify-content:space-between;
                         gap:0.6rem; margin-bottom:0.5rem; }
    .ia-tcard .tc-name { font-size:0.98rem; font-weight:700; color:var(--td-text); }
    .ia-tcard .tc-badge { flex-shrink:0; font-size:0.72rem; font-weight:600;
                          padding:0.14rem 0.6rem; border-radius:999px; }
    .ia-tcard .tc-badge.kb { background:#E6F7F0; color:#00875A; border:1px solid #BDE8D4; }
    .ia-tcard .tc-badge.ai { background:#FFF4E8; color:#D2661A; border:1px solid #FAD8B4; }
    .ia-tcard .tc-tags { display:flex; flex-wrap:wrap; gap:0.4rem; margin-bottom:0.55rem; }
    .ia-tcard .tc-tag { font-size:0.74rem; font-weight:600; padding:0.12rem 0.55rem;
                        border-radius:6px; background:var(--td-brand-light); color:var(--td-brand); }
    .ia-tcard .tc-tag.loc { background:var(--td-bg); color:var(--td-muted); font-weight:500; }
    .ia-tcard .tc-line { font-size:0.83rem; line-height:1.55; color:var(--td-text);
                         margin-top:0.3rem; }
    .ia-tcard .tc-k { display:inline-block; font-size:0.72rem; font-weight:600;
                      color:var(--td-muted); background:var(--td-bg); border-radius:5px;
                      padding:0.05rem 0.45rem; margin-right:0.4rem; }
    </style>
    """, unsafe_allow_html=True)
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


def render_input_panel(run_label: str):
    """材料输入面板：输入页与报告页「重新梳理」共用。
    返回 (material, run_clicked, focus_hint, region, park_level, park_city, local_only)"""
    input_col, opt_col = st.columns([3, 1], gap="large")
    with input_col:
        st.markdown('<div class="ia-card">', unsafe_allow_html=True)
        st.markdown('<div class="ia-card-title">📄 园区材料</div>'
                    '<div class="ia-card-desc">粘贴企业目录、园区介绍等文字材料，或上传文件</div>',
                    unsafe_allow_html=True)
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
            up = st.file_uploader(
                "上传 .txt / .csv / .xlsx / .pdf / .docx 文件",
                type=["txt", "csv", "xlsx", "pdf", "docx"],
                label_visibility="collapsed")
            st.caption("图片（JPG / PNG）材料请直接粘贴图中文字。")
            if up is not None:
                # 同一文件只处理一次，避免上传器在 rerun 后重复触发
                _fid = getattr(up, "file_id", up.name)
                if st.session_state.get("_processed_upload") != _fid:
                    st.session_state["_processed_upload"] = _fid
                    try:
                        if up.name.endswith(".txt"):
                            uploaded_text = up.read().decode("utf-8", errors="ignore")
                        elif up.name.endswith(".pdf"):
                            from pypdf import PdfReader
                            _reader = PdfReader(up)
                            uploaded_text = "\n".join(
                                (_pg.extract_text() or "") for _pg in _reader.pages)
                        elif up.name.endswith(".docx"):
                            from docx import Document
                            _doc = Document(up)
                            uploaded_text = "\n".join(
                                _p.text for _p in _doc.paragraphs if _p.text.strip())
                        else:
                            import pandas as pd
                            df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
                            uploaded_text = df.to_string(index=False)
                        if not (uploaded_text or "").strip():
                            st.error("未能从文件中提取到文字内容，请尝试粘贴文本或换个文件")
                            uploaded_text = ""
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
            else:
                material = st.session_state.get("industry_material", "")

        _q = analyze_material_quality(material or "")
        if _q["enterprises"]:
            _q_parts = [f"已识别约 {_q['enterprises']} 家企业"]
            if _q["with_scale"]:
                _q_parts.append(f"{_q['with_scale']} 家含规模信息")
            if _q["with_qualification"]:
                _q_parts.append(f"{_q['with_qualification']} 家含资质信息")
            st.caption("✅ " + "，".join(_q_parts) +
                       ("。" if (_q["with_scale"] or _q["with_qualification"]) else
                        "，建议补充产值 / 员工数 / 资质，报告会更准。"))

        btn_col, tip_col = st.columns([1, 2])
        with btn_col:
            run_clicked = st.button(run_label, type="primary", use_container_width=True)
        with tip_col:
            if st.button("📋 填入示例材料", use_container_width=True):
                st.session_state["_fill_example"] = True
                st.rerun()

        with st.expander("📋 支持什么材料？三档规范（材料越全，报告越准）"):
            st.markdown(MATERIAL_GUIDE)
            st.download_button("⬇ 下载企业清单模板（CSV）", TEMPLATE_CSV,
                               "企业清单模板.csv", "text/csv",
                               use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with opt_col:
        with st.expander("⚙️ 园区背景（可选）", expanded=not result_exists()):
            st.caption("提供背景可让分类与招商建议更贴合园区实际。")
            park_city = st.text_input("所在城市", placeholder="如：合肥")
            park_level = st.selectbox("园区级别",
                                      ["未指定", "国家级", "省级", "市级", "区县级"])
            focus_hint = st.text_input("产业方向提示", placeholder="如：锂电新材料")
            region = st.text_input("目标招商区域", placeholder="如：长三角 / 不限")
            local_only = st.checkbox("🔒 敏感材料本地处理", value=False,
                                     help="开启后完全禁止调用外部 LLM，材料零出域；"
                                          "结果为本地规则生成（分类/环节归位可用，AI 补全类内容不生成）")
    return material, run_clicked, focus_hint, region, park_level, park_city, local_only


def result_exists() -> bool:
    return bool(st.session_state.get("industry_analysis_result"))


# ---------------------------------------------------------------- 标题区
result = st.session_state.get("industry_analysis_result")

_mode_llm = bool(result and result.get("mode") == "llm" and not result.get("llm_error"))
_badge_cls = "ia-mode-llm" if _mode_llm else "ia-mode-tpl"
_badge_txt = ("🔒 本地模式 · 材料不出本机" if result and result.get("local_only")
              else ("🟢 智能模式" if _mode_llm else "⚪ 本地模式"))

st.markdown(f"""
<div class="ia-page-header">
    <div>
        <div class="ia-title">🧭 产业智能梳理</div>
        <div class="ia-subtitle">粘贴一份园区企业材料，自动生成产业分类、上中下游环节诊断、
        强链补链延链路径、招商目标企业清单与研究院/协会资源。</div>
    </div>
    <div class="ia-mode-badge {_badge_cls}">{_badge_txt}</div>
</div>
""", unsafe_allow_html=True)

# 智能模式调用失败 → 明确告知本次由本地引擎兜底（不静默）
if result and result.get("llm_error"):
    st.warning(f"⚠️ 智能模式本次调用失败，已改用本地引擎生成：{result['llm_error']}")

# 会话写入须在文本域等组件创建之前完成（Streamlit 禁止对已实例化组件的 key 赋值）：
# 用标志位 + rerun 的方式，在脚本最前置位应用填入内容
if st.session_state.pop("_fill_example", None):
    st.session_state["industry_material"] = EXAMPLE_MATERIAL
    st.session_state["_notice"] = "已填入示例材料，可直接点击「开始产业梳理」"
if st.session_state.pop("_fill_upload", None):
    st.session_state["industry_material"] = st.session_state.pop("_uploaded_text", "")
# 演示版：首次进入自动填入示例材料，客户零输入、一键体验完整链路
if get_app_mode() == "demo" and "industry_material" not in st.session_state:
    st.session_state["industry_material"] = EXAMPLE_MATERIAL
_notice = st.session_state.pop("_notice", None)
if _notice:
    st.success(_notice)

# 侧边栏二级目录：输入页显示步骤说明，报告页显示可点击的报告结构
with st.sidebar:
    if result:
        st.markdown("**📋 报告结构**")
        st.markdown(
            '<div style="font-size:0.85rem;line-height:2">'
            '<a href="#ia-sec-classify">一、产业分类</a><br>'
            '<a href="#ia-sec-chain">二、产业链上下游分析</a><br>'
            '<a href="#ia-sec-advice">三、产业发展建议</a><br>'
            '<a href="#ia-sec-invest">四、产业招商推荐</a><br>'
            '<a href="#ia-export">导出报告</a></div>',
            unsafe_allow_html=True)
    else:
        st.markdown("**📋 梳理步骤**\n\n"
                    "1. 提供园区材料\n2. 产业分类\n3. 产业链上下游分析\n"
                    "4. 产业发展建议\n5. 产业招商推荐")

# ---------------------------------------------------------------- 两阶段结构：输入页 / 报告页
if result:
    # 报告页顶部：材料摘要 + 重新梳理入口
    _mat = st.session_state.get("industry_analysis_material", "")
    _qq = analyze_material_quality(_mat)
    _gen = st.session_state.get("industry_analysis_time", "")
    _summ = f"📄 本次材料：{len(_mat)} 字符 · 约 {_qq['enterprises']} 家企业"
    if _gen:
        _summ += f" · 生成于 {_gen}"
    st.markdown(f'<div class="ia-tip"><span>{_summ}</span></div>',
                unsafe_allow_html=True)
    with st.expander("⚙️ 修改材料 / 调整背景，重新梳理"):
        _panel = render_input_panel("🔄 重新梳理")
else:
    _panel = render_input_panel("🚀 开始产业梳理")
material, run_clicked, focus_hint, region, park_level, park_city, local_only = _panel

# ---------------------------------------------------------------- 运行分析
if run_clicked:
    if not (material or "").strip():
        st.warning("请先粘贴材料或上传文件")
    else:
        _bg = []
        if park_level and park_level != "未指定":
            _bg.append(f"{park_level}园区")
        if (park_city or "").strip():
            _bg.append("位于" + park_city.strip())
        if (region or "").strip():
            _bg.append("招商目标区域：" + region.strip())
        region_ctx = "；".join(_bg)
        with st.status("正在进行产业梳理，请稍候…", expanded=True) as status:
            result = run_industry_analysis(material.strip(), focus_hint.strip(),
                                           region_ctx, local_only=local_only)
            status.update(label="梳理完成", state="complete")
        st.session_state["industry_analysis_result"] = result
        st.session_state["industry_analysis_material"] = material.strip()
        st.session_state["industry_analysis_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.rerun()

if not result:
    st.markdown('<div class="ia-tip">👆 提供材料后点击「开始产业梳理」。可点「📋 填入示例材料」快速体验完整流程。</div>',
                unsafe_allow_html=True)
    st.stop()

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

# ---------------------------------------------------------------- 一、产业分类
st.markdown('<div id="ia-sec-classify"></div>', unsafe_allow_html=True)
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

# ---------------------------------------------------------------- 二、产业链上下游分析
st.markdown('<div id="ia-sec-chain"></div>', unsafe_allow_html=True)
st.markdown('<div class="ia-section"><span class="ia-section-num">二</span>'
            '<span class="ia-section-title">产业链上下游分析</span>'
            '<span class="ia-section-note">上中下游环节分布 · 缺失环节已标红</span></div>',
            unsafe_allow_html=True)
if gaps.get("is_template"):
    st.markdown('<div class="ia-tip">本地模式按关键词归位，环节较粗；智能模式下输出细化环节（如"正极材料""电芯"级）并判定真实缺失环节。</div>',
                unsafe_allow_html=True)
render_chain_map(result["chain_map"], gaps)

# ---------------------------------------------------------------- 三、产业发展建议
st.markdown('<div id="ia-sec-advice"></div>', unsafe_allow_html=True)
st.markdown('<div class="ia-section"><span class="ia-section-num">三</span>'
            '<span class="ia-section-title">产业发展建议</span>'
            '<span class="ia-section-note">强链 · 补链 · 延链</span></div>',
            unsafe_allow_html=True)
render_path_cards(result.get("paths", {}))

# ---------------------------------------------------------------- 四、产业招商推荐
st.markdown('<div id="ia-sec-invest"></div>', unsafe_allow_html=True)
st.markdown('<div class="ia-section"><span class="ia-section-num">四</span>'
            '<span class="ia-section-title">产业招商推荐</span>'
            '<span class="ia-section-note">目标企业 · 研究院/协会资源</span></div>',
            unsafe_allow_html=True)
if result.get("targets"):
    n_kb = sum(1 for t in result["targets"] if t.get("source") == "知识库")
    n_ai = len(result["targets"]) - n_kb
    st.markdown('<div class="ia-alert">🟢 <b>知识库条目</b>：人工整理、已核实，对接前建议复核最新动态；'
                '🟠 <b>AI 生成条目</b>：基于公开信息生成，企业名称、所在地与落地线索请在正式对接前逐一人工核实。</div>',
                unsafe_allow_html=True)
    render_target_cards(result["targets"])
    st.caption(f"共 {len(result['targets'])} 家目标企业：知识库已核实 {n_kb} 家"
               + (f"，AI 生成待核实 {n_ai} 家" if n_ai else ""))
else:
    st.markdown('<div class="ia-tip">本次未生成招商目标清单。可在 <code>data/invest_targets.json</code> 中'
                '维护已核实目标企业（按「产业 → 环节 → 企业」），或启用智能模式由 AI 自动补全。</div>',
                unsafe_allow_html=True)

# 研究院 / 协会资源（产业招商推荐的配套对接线索）
res = result.get("resources", {})
if res:
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
else:
    st.markdown('<div class="ia-tip">未命中本地产业资源知识库。可在 <code>data/industry_resources.json</code> 中按产业维护'
                '已核实的研究院、协会与联盟，或启用智能模式由 AI 自动梳理该产业有影响力的机构。</div>',
                unsafe_allow_html=True)

# ---------------------------------------------------------------- 导出
st.markdown('<div id="ia-export"></div>', unsafe_allow_html=True)
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
