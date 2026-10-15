"""
产业智能梳理
============
面向园区的"材料 → 洞察"入口：粘贴企业目录或文字材料，
智能体自动完成产业分类 → 上中下游环节梳理 → 强弱缺失分析
→ 强链补链延链路径 → 招商目标企业清单 → 研究院/协会资源。

配置 ANTHROPIC_API_KEY / OPENAI_API_KEY 后为 LLM 全链路；
无 Key 时自动降级为模板模式（基础归位，目标企业与资源待 LLM 生成）。
"""

import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.industry_analyzer import run_industry_analysis, to_markdown

st.set_page_config(
    page_title="产业智能梳理 - 园区产业分析智能体",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

st.markdown('<div class="main-title">🧭 产业智能梳理</div>', unsafe_allow_html=True)
st.markdown(
    "<p style='color: var(--apple-muted);'>提供园区企业目录、文字版材料等基础资料，"
    "智能体自动完成：产业分类 → 上中下游分环节梳理 → 强弱缺失分析 → "
    "强链补链延链路径 → 招商目标企业清单 + 研究院/协会资源。</p>",
    unsafe_allow_html=True,
)

st.divider()

# ---------------- 第一步：材料输入 ----------------
st.markdown("### 第一步：提供园区材料")

col_input, col_opt = st.columns([3, 1])

with col_opt:
    st.markdown("**辅助信息（可选）**")
    focus_hint = st.text_input("产业方向提示", placeholder="如：锂电新材料",
                               help="帮助智能体聚焦主导产业，分类更准确")
    region = st.text_input("目标招商区域", placeholder="如：长三角 / 珠三角 / 不限",
                           help="生成招商目标企业清单时优先该区域及邻近城市")
    if st.button("📋 填入示例材料", use_container_width=True):
        st.session_state["industry_material"] = EXAMPLE_MATERIAL
        st.rerun()

with col_input:
    material = st.text_area(
        "粘贴企业目录 / 园区介绍 / 文字材料",
        height=260,
        key="industry_material",
        placeholder="每行一家企业最佳，也支持整段文字材料；或从下方上传文件",
    )
    up = st.file_uploader("或上传文件（.txt / .csv / .xlsx）", type=["txt", "csv", "xlsx"])
    if up is not None:
        try:
            if up.name.endswith(".txt"):
                material = up.read().decode("utf-8", errors="ignore")
            else:
                import pandas as pd
                df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
                material = df.to_string(index=False)
            st.success(f"已读取文件：{up.name}（{len(material)} 字符）")
        except Exception as e:
            st.error(f"文件读取失败：{e}")

st.divider()

# ---------------- 运行分析 ----------------
if st.button("🚀 开始产业梳理", type="primary", use_container_width=True, disabled=not material.strip()):
    if not material.strip():
        st.warning("请先粘贴材料或上传文件")
    else:
        with st.status("正在进行产业梳理，请稍候…", expanded=True) as status:
            result = run_industry_analysis(material, focus_hint.strip(), region.strip())
            status.update(label="梳理完成", state="complete")
        st.session_state["industry_analysis_result"] = result
        st.session_state["industry_analysis_material_len"] = len(material)

# ---------------- 结果展示 ----------------
result = st.session_state.get("industry_analysis_result")
if not result:
    st.info("👆 提供材料后点击「开始产业梳理」。可先点「填入示例材料」体验完整流程。")
    st.stop()

is_llm = result.get("mode") == "llm"
badge = "🟢 LLM 智能模式" if is_llm else "🟡 模板模式（未配置 API Key）"
st.markdown(f"**生成模式**：{badge}")

# ① 产业分类
st.markdown("## ① 产业分类结果")
for group in result["classification"].get("industries", []):
    ents = group.get("enterprises", [])
    with st.expander(f"**{group['industry']}**（{len(ents)} 家企业）", expanded=True):
        rows = [{"企业名称": e.get("name", ""), "主要产品": e.get("products", ""),
                 "核心技术": e.get("tech", ""), "规模": e.get("scale", "")} for e in ents]
        st.dataframe(rows, use_container_width=True, hide_index=True)

# ② 上中下游环节梳理
st.markdown("## ② 上中下游环节梳理")
gaps = result.get("gaps", {})
cols = st.columns(3)
layer_meta = {"上游": "🌾 上游 · 原材料/装备", "中游": "⚙️ 中游 · 制造/集成", "下游": "🚀 下游 · 应用/服务"}
for col, (layer, title) in zip(cols, layer_meta.items()):
    with col:
        segs = [s for s in result["chain_map"].get("segments", []) if s.get("layer") == layer]
        body = []
        for s in segs:
            n = len(s.get("enterprises", []))
            tag = f"（{n} 家）" if n else "（**缺失**）"
            body.append(f"- **{s['segment']}**{tag}：" + ("、".join(s["enterprises"]) if n else "尚无企业布局"))
        st.markdown(f"**{title}**\n\n" + ("\n".join(body) if body else "- （无企业布局）"))
st.caption("💡 强弱缺失分析：" +
           (f"薄弱环节（仅 1 家）：{'、'.join(gaps.get('weak_segments', [])) or '无'}；"
            f"缺失环节：{'、'.join(gaps.get('empty_segments', [])) or '无'}"
            if not gaps.get("is_template") else
            "模板模式按关键词归位，缺失环节判定与环节细化需 LLM 模式（配置 API Key）"))

# ③ 强链补链延链
st.markdown("## ③ 强链补链延链路径")
paths = result.get("paths", {})
pcols = st.columns(3)
path_meta = [("🔧 强链", "strengthen", "巩固优势环节"),
             ("🧩 补链", "complete", "招引缺失环节"),
             ("➡️ 延链", "extend", "向高附加值延伸")]
for col, (title, key, subtitle) in zip(pcols, path_meta):
    with col:
        items = paths.get(key, [])
        md = [f"**{title}** · {subtitle}"]
        for it in items:
            head = it.get("segment") or it.get("direction", "")
            md.append(f"- **{head}**：{it.get('action', '')}  \n  依据：{it.get('rationale', '')}")
        st.markdown("\n\n".join(md) if len(md) > 1 else f"**{title}**\n\n- （暂无）")

# ④ 招商目标企业清单
st.markdown("## ④ 招商目标企业清单")
if result.get("targets"):
    st.warning("⚠️ 目标清单由 AI 生成，对接前请逐一核实企业真实性与落地意愿。", icon=None)
    trows = [{"目标企业": t.get("name", ""), "对应环节": t.get("segment", ""),
              "所在地": t.get("region", ""), "配套逻辑": t.get("reason", ""),
              "落地线索": t.get("signal", "")} for t in result["targets"]]
    st.dataframe(trows, use_container_width=True, hide_index=True)
else:
    st.info("模板模式未生成目标企业清单。配置 ANTHROPIC_API_KEY / OPENAI_API_KEY 后，"
            "将基于缺失/薄弱环节自动生成真实目标企业（含所在地、配套逻辑与落地线索）。")

# ⑤ 研究院/协会资源
st.markdown("## ⑤ 研究院 / 协会资源")
res = result.get("resources", {})
if res:
    rcols = st.columns(2)
    with rcols[0]:
        st.markdown("**🔬 研究机构**")
        for i in res.get("institutes", []):
            st.markdown(f"- **{i.get('name', '')}**（{i.get('location', '')}）  \n  {i.get('focus', '')}")
    with rcols[1]:
        st.markdown("**🏛️ 行业组织**")
        for a in res.get("associations", []):
            st.markdown(f"- **{a.get('name', '')}**  \n  {a.get('focus', '')}")
else:
    st.info("模板模式未生成产业资源清单。配置 API Key 后自动梳理可对接的研究院与协会。")

# 导出
st.divider()
md_report = to_markdown(result)
st.download_button("📥 导出梳理报告（Markdown）", data=md_report.encode("utf-8"),
                   file_name="产业梳理报告.md", mime="text/markdown")
