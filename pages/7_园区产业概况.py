"""
园区产业概况
============
单页五段式：填入基本信息 → 产业分类 → 产业链上下游分析 → 产业发展建议 → 产业招商推荐。
全部内容在本页面内自上而下生成，左侧导航与页内步骤条仅做锚点滚动定位，不跳转新页面。
"""

from datetime import datetime

import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.auth import require_auth
try:  # 兼容部署环境中尚未热更新的旧版 auth 模块（缺 get_app_mode 时降级为演示模式）
    from engine.auth import get_app_mode
except ImportError:
    def get_app_mode() -> str:
        return "demo"
from engine.industry_analyzer import run_industry_analysis
from engine import ia_history
from engine.ia_sections import (
    inject_ia_css, render_ia_header, render_kpi_strip,
    render_classification, render_chain_analysis, render_paths_section,
    render_targets_section, render_resources_subsection, render_export_block,
    analyze_material_quality, RESULT_KEY,
)
try:  # 滚动定位为增强功能：部署缓存中偶发旧版模块时降级为空操作，不影响主流程
    from engine.ia_sections import scroll_to_anchor
except ImportError:  # pragma: no cover
    def scroll_to_anchor() -> None:
        pass

st.set_page_config(page_title="园区产业概况", page_icon="🏭", layout="wide")
inject_apple_theme()
inject_ia_css()
require_auth()
st.session_state["_page_id"] = "overview"

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

# 原始文稿示例：模拟公众号/园区动态的真实混乱格式（无编号、信息嵌在段落里），
# 用于演示智能模式从乱材料中提取企业信息的能力
MESSY_EXAMPLE = """【园区动态】聚焦新能源新材料，我区集聚效应初步显现
近年来，我区聚焦新能源新材料主导产业，坚持招大引强、集群发展，产业集聚效应初步显现。目前区内已集聚一批产业链上下游企业，涵盖正极材料、负极材料、电解液、隔膜、电芯、系统集成等关键环节。

在正极材料环节，安徽金泉新材料有限公司主要从事正极材料前驱体的研发生产，去年产值约8亿元，今年还在扩产。负极这块主要是硅源纳米科技（合肥）有限公司，做硅碳负极，核心团队来自中国科学技术大学，目前处于产能爬坡阶段。电解液由皖江电解液科技有限公司供货，是几家头部电池厂的合格供应商。隔膜厂安徽蓝科隔膜材料有限公司去年年底刚投产。

电芯厂是合肥星恒电芯制造有限公司，主做磷酸铁锂；Pack集成可以找安徽聚能电池系统有限公司，两家一直有配套合作。设备与检测环节有合肥精测仪器股份有限公司（电池检测设备）和皖江智能装备有限公司（材料产线设备）。另外，安徽循环再生科技有限公司做退役电池回收梯次利用，合肥新能物流有限公司负责危化品仓储运输。

据了解，目前园区在正负极头部企业、隔膜涂覆等环节仍存在短板，下一步将围绕补齐产业链短板精准招商……
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


def render_input_panel(run_label: str, has_result: bool):
    """材料输入面板。返回 (material, run_clicked, focus_hint, region, park_level, park_city, local_only)"""
    input_col, opt_col = st.columns([3, 1], gap="large")
    with input_col:
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

        btn_col, ex_col, messy_col = st.columns([1.2, 1, 1])
        with btn_col:
            run_clicked = st.button(run_label, type="primary", use_container_width=True)
        with ex_col:
            if st.button("📋 填入示例材料", use_container_width=True):
                st.session_state["_fill_example"] = True
                st.rerun()
        with messy_col:
            if st.button("📄 填入原始文稿", use_container_width=True):
                st.session_state["_fill_messy"] = True
                st.rerun()

        with st.expander("📋 支持什么材料？三档规范（材料越全，报告越准）"):
            st.markdown(MATERIAL_GUIDE)
            st.download_button("⬇ 下载企业清单模板（CSV）", TEMPLATE_CSV,
                               "企业清单模板.csv", "text/csv",
                               use_container_width=True)

    with opt_col:
        with st.expander("⚙️ 园区背景（可选）", expanded=not has_result):
            park_city = st.text_input("所在城市", placeholder="如：合肥")
            park_level = st.selectbox("园区级别",
                                      ["未指定", "国家级", "省级", "市级", "区县级"])
            focus_hint = st.text_input("产业方向提示", placeholder="如：锂电新材料")
            region = st.text_input("目标招商区域", placeholder="如：长三角 / 不限")
            local_only = st.checkbox("🔒 敏感材料本地处理", value=False,
                                     help="开启后完全禁止调用外部 LLM，材料零出域；"
                                          "结果为本地规则生成（分类/环节归位可用，AI 补全类内容不生成）")
    return material, run_clicked, focus_hint, region, park_level, park_city, local_only


# ---------------------------------------------------------------- 标题区
result = st.session_state.get(RESULT_KEY)
# 启动自动恢复：无会话结果时载入最近一次梳理记录（内部试用，刷新/重启不丢）
if not result:
    _latest = ia_history.latest_record()
    if _latest:
        st.session_state[RESULT_KEY] = _latest["result"]
        st.session_state["industry_analysis_material"] = _latest.get("material", "")
        st.session_state["industry_analysis_time"] = _latest.get("saved_at", "")
        # 记录是完整成果：直接恢复全部分区全景，不必从②步重走
        st.session_state["ia_step"] = 5
        st.session_state["ia_current"] = 2
        result = _latest["result"]

render_ia_header(
    "🏭 园区产业概况",
    "单页完成全流程：填入园区材料并运行梳理，产业分类、产业链分析、发展建议与"
    "招商推荐依次在本页生成，可点上方步骤条回到任意步骤修改。",
    result,
)

# 侧栏 / 步骤条经查询参数（ia_step）定位时，自动展开到对应步骤
_qp_step = st.query_params.get("ia_step")
if _qp_step and result:
    try:
        st.session_state["ia_step"] = max(int(_qp_step),
                                          st.session_state.get("ia_step") or 2)
        st.session_state["ia_current"] = int(_qp_step)
    except (TypeError, ValueError):
        pass


def _render_advance(next_step: int, label: str) -> None:
    """分步推进：主按钮展开下一部分，副按钮一次展开全部。"""
    c1, c2, _ = st.columns([1.3, 1.3, 2.6])
    with c1:
        if st.button(f"下一步：{label} →", key=f"ia_adv_{next_step}", type="primary",
                     use_container_width=True):
            st.session_state["ia_step"] = next_step
            st.session_state["ia_current"] = next_step
            st.rerun()
    with c2:
        if st.button("⤵ 一次展开全部", key=f"ia_adv_all_{next_step}",
                     use_container_width=True):
            st.session_state["ia_step"] = 5
            st.rerun()

# ---------------------------------------------------------------- 侧栏：梳理记录（历史保存 / 载入 / 删除）
_records = ia_history.list_records()
with st.sidebar:
    st.markdown("🗂 **梳理记录**")
    _sel = None
    _load_clicked = _del_clicked = False
    if _records:
        _sel = st.selectbox("历史记录", [r["name"] for r in _records],
                            label_visibility="collapsed")
        _hc1, _hc2 = st.columns(2)
        with _hc1:
            _load_clicked = st.button("📂 载入", use_container_width=True)
        with _hc2:
            _del_clicked = st.button("🗑 删除", use_container_width=True)
    else:
        st.caption("暂无记录，运行梳理后自动保存")

# ---------------------------------------------------------------- 状态化步骤条
# 状态模型：ia_step = 已解锁到的最大步（门控渲染）；ia_current = 正在查看的位置（高亮）
# 每步三态：✓ 已完成（可点，滚回查看）/ ● 当前（主按钮高亮）/ 未解锁（置灰不可点）
_STEP_ITEMS = [
    (1, "① 填入基本信息", "ia-input"),
    (2, "② 产业分类", "ia-sec-class"),
    (3, "③ 产业链分析", "ia-sec-chain"),
    (4, "④ 产业发展建议", "ia-sec-paths"),
    (5, "⑤ 产业招商推荐", "ia-sec-invest"),
]


def _open_edit() -> None:
    """展开①输入编辑区，并记住当前查看位置以便收起时还原。"""
    if st.session_state.get("ia_current", 2) != 1:
        st.session_state["_ia_prev_current"] = \
            st.session_state.get("ia_current") or 2
    st.session_state["_edit_mode"] = True
    st.session_state["ia_current"] = 1
    st.session_state["_scroll_target"] = "ia-input"
    st.rerun()


def _close_edit() -> None:
    """收起输入编辑区，还原到展开前查看的步骤。"""
    st.session_state["_edit_mode"] = False
    st.session_state["ia_current"] = st.session_state.pop("_ia_prev_current", None) or 2
    st.rerun()


if result:
    _ia_step = st.session_state.get("ia_step") or 2
    _ia_cur = st.session_state.get("ia_current") or 2
    _in_edit = bool(st.session_state.get("_edit_mode"))
    _sb_cols = st.columns(5)
    for (_no, _label, _anchor), _col in zip(_STEP_ITEMS, _sb_cols):
        with _col:
            if _no == 1:
                # 输入步：编辑中为「当前」，否则视为已完成
                _is_cur = _in_edit
                if st.button(("● " if _is_cur else "✓ ") + _label,
                             key="ia_sb_1",
                             type="primary" if _is_cur else "secondary",
                             use_container_width=True):
                    _open_edit()
            elif _no > _ia_step:
                st.button(_label, key=f"ia_sb_{_no}", disabled=True,
                          use_container_width=True)
            else:
                _is_cur = (_no == _ia_cur) and not _in_edit
                if st.button(("● " if _is_cur else "✓ ") + _label,
                             key=f"ia_sb_{_no}",
                             type="primary" if _is_cur else "secondary",
                             use_container_width=True):
                    st.session_state["ia_current"] = _no
                    st.session_state["_scroll_target"] = _anchor
                    st.rerun()
    _done_n = 1 + sum(1 for _n, _, _ in _STEP_ITEMS
                      if _n >= 2 and _n <= _ia_step)
    st.caption(f"进度：已完成 {_done_n}/5 步 · "
             + ("正在修改①材料" if _in_edit
                else f"当前位于 {_STEP_ITEMS[_ia_cur - 1][1]}"))
else:
    st.markdown('<div class="ia-tip">👇 在下方填入园区材料并运行梳理，'
                '②–⑤ 各部分报告将在<b>本页面内</b>依次生成；'
                '完成后可点上方步骤条回到任意步骤修改。</div>',
                unsafe_allow_html=True)

# 会话写入须在文本域等组件创建之前完成（Streamlit 禁止对已实例化组件的 key 赋值）：
# 用标志位 + rerun 的方式，在脚本最前置位应用填入内容
if st.session_state.pop("_fill_example", None):
    st.session_state["industry_material"] = EXAMPLE_MATERIAL
    st.session_state["_notice"] = "已填入示例材料，可直接点击「开始产业梳理」"
if st.session_state.pop("_fill_messy", None):
    st.session_state["industry_material"] = MESSY_EXAMPLE
    st.session_state["_notice"] = "已填入原始文稿示例（格式较乱，适合体验智能模式的信息提取）"
if st.session_state.pop("_fill_upload", None):
    st.session_state["industry_material"] = st.session_state.pop("_uploaded_text", "")
# 演示版：首次进入自动填入示例材料，客户零输入、一键体验完整链路
if get_app_mode() == "demo" and "industry_material" not in st.session_state:
    st.session_state["industry_material"] = EXAMPLE_MATERIAL
_notice = st.session_state.pop("_notice", None)
if _notice:
    st.success(_notice)

# ---------------------------------------------------------------- ① 填入基本信息（已有结果时默认收起，经「修改材料」按钮或步骤条①展开）
st.markdown('<div id="ia-input"></div>', unsafe_allow_html=True)
if result:
    _mat = st.session_state.get("industry_analysis_material", "")
    _qq = analyze_material_quality(_mat)
    _gen = st.session_state.get("industry_analysis_time", "")
    _summ = f"📄 本次材料：{len(_mat)} 字符 · 约 {_qq['enterprises']} 家企业"
    if _gen:
        _summ += f" · 生成于 {_gen}"
    st.markdown(f'<div class="ia-tip"><span>{_summ}</span></div>',
                unsafe_allow_html=True)
# 编辑模式（步骤条「① 填入基本信息」或下方按钮触发）：展开输入区供修改重跑
if result and not st.session_state.get("_edit_mode"):
    if st.button("⚙️ 修改材料 / 调整背景，重新梳理", key="ia_open_input"):
        _open_edit()
    _panel = ("", False, "", "", "未指定", "", False)
else:
    _panel = render_input_panel("🔄 重新梳理" if result else "🚀 开始产业梳理",
                                has_result=bool(result))
    if result and st.button("✖ 收起输入区", key="ia_collapse_input"):
        _close_edit()
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
        st.session_state[RESULT_KEY] = result
        st.session_state["industry_analysis_material"] = material.strip()
        st.session_state["industry_analysis_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state["ia_step"] = 2  # 分步呈现：先出 ② 产业分类
        st.session_state["ia_current"] = 2
        st.session_state["_edit_mode"] = False  # 收起输入区，直接展示新结果
        st.session_state.pop("_ia_prev_current", None)
        # 自动保存为历史记录（同名覆盖；默认以城市命名，便于多园区管理）
        _rec_name = (park_city.strip() + "产业园区") if (park_city or "").strip() \
            else f"梳理记录 {st.session_state['industry_analysis_time']}"
        ia_history.save_record(_rec_name, result, material.strip())
        st.session_state["ia_record_name"] = _rec_name
        st.session_state["_notice"] = f"梳理完成，已保存至「{_rec_name}」（左侧 🗂 可载入历史记录）"
        st.rerun()

# ---------------------------------------------------------------- 历史记录：载入 / 删除
if _load_clicked and _sel:
    _rec = ia_history.load_record(_sel)
    if _rec:
        st.session_state[RESULT_KEY] = _rec["result"]
        st.session_state["industry_analysis_material"] = _rec.get("material", "")
        st.session_state["industry_analysis_time"] = _rec.get("saved_at", "")
        st.session_state["ia_record_name"] = _sel
        # 记录是完整成果：直接展开全部，不必从②步逐个点「下一步」
        st.session_state["ia_step"] = 5
        st.session_state["ia_current"] = 2
        st.session_state["_edit_mode"] = False
        st.session_state["_notice"] = f"已载入记录「{_sel}」（{_rec.get('saved_at', '')}）"
        st.rerun()
if _del_clicked and _sel:
    ia_history.delete_record(_sel)
    st.session_state["_notice"] = f"已删除记录「{_sel}」"
    if st.session_state.get("ia_record_name") == _sel:
        for _k in (RESULT_KEY, "industry_analysis_material",
                   "industry_analysis_time", "ia_record_name",
                   "ia_step", "ia_current", "_edit_mode", "_ia_prev_current"):
            st.session_state.pop(_k, None)
    st.rerun()

# ---------------------------------------------------------------- ②–⑤ 同页分步生成报告各部分
if result:
    render_kpi_strip(result)
    step = st.session_state.get("ia_step") or 2

    st.markdown('<div id="ia-sec-class"></div>', unsafe_allow_html=True)
    render_classification(result)
    # 产业梳理 → 企业诊断 打通：选择园区内企业一键送入诊断
    _ent_rows = [(g.get("industry", ""), e)
                 for g in result["classification"].get("industries", [])
                 for e in g.get("enterprises", [])]
    if _ent_rows:
        _d1, _d2 = st.columns([3, 1])
        with _d1:
            _pick = st.selectbox("🩺 选择园区内企业，直接进行政策诊断",
                                 options=[""] + [e.get("name", "") for _, e in _ent_rows],
                                 format_func=lambda x: x or "（选择企业）")
        with _d2:
            st.write("")
            _go_diag = st.button("进入诊断 →", key="ia_go_diag",
                                 use_container_width=True, disabled=not _pick)
        if _go_diag and _pick:
            _ind, _ent = next((i, e) for i, e in _ent_rows if e.get("name") == _pick)
            st.session_state["pending_diag_profile"] = {
                "name": _ent.get("name", ""),
                "industry": _ind,
                "sub_industry": _ind,
                "core_product": _ent.get("products", ""),
            }
            st.switch_page("pages/6_企业诊断辅导.py")
    if step == 2:
        _render_advance(3, "③ 产业链分析")

    if step >= 3:
        st.markdown('<div id="ia-sec-chain"></div>', unsafe_allow_html=True)
        render_chain_analysis(result)
        if step == 3:
            _render_advance(4, "④ 产业发展建议")

    if step >= 4:
        st.markdown('<div id="ia-sec-paths"></div>', unsafe_allow_html=True)
        render_paths_section(result)
        if step == 4:
            _render_advance(5, "⑤ 产业招商推荐")

    if step >= 5:
        st.markdown('<div id="ia-sec-invest"></div>', unsafe_allow_html=True)
        render_targets_section(result)
        render_resources_subsection(result)
        render_export_block(result)

# ---------------------------------------------------------------- 侧栏步骤按钮触发的滚动定位（无刷新）
scroll_to_anchor()

