import json
import os
from datetime import datetime

import streamlit as st
import plotly.graph_objects as go

from engine.ui_helpers import inject_apple_theme
from engine.matcher import load_json
from engine.diagnosis import run_enhanced_diagnosis, get_api_config
from engine.dashboard import compute_dashboard_metrics, sort_results_for_display
from engine.radar_chart import calculate_dimension_scores, build_radar_chart, fig_to_image_bytes
from engine.report_export import (
    build_markdown_report,
    build_word_report,
    build_pdf_report,
    select_top3_policies,
)
from engine.cultivation_roadmap import (
    generate_enterprise_roadmap,
    save_roadmap,
    build_roadmap_markdown,
    PHASE_LABELS,
    PHASE_ORDER,
)
from engine.llm_scorer import generate_material_outline

st.set_page_config(
    page_title="企业诊断辅导 - 园区产业分析智能体",
    page_icon="🩺",
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
.metric-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow-sm);
    text-align: center;
}
.metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--apple-text);
}
.metric-label {
    font-size: 0.85rem;
    color: var(--apple-muted);
    margin-top: 0.25rem;
}
.status-immediate { color: #34c759; }
.status-cultivate { color: #ff9500; }
.status-watch { color: #0071e3; }
.status-unsuitable { color: #ff3b30; }
.result-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow-sm);
}
.phase-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1.1rem 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow-sm);
}
.action-title { font-weight: 600; margin-bottom: 0.35rem; }
.action-meta { color: var(--apple-muted); font-size: 0.85rem; margin-bottom: 0.5rem; }
.tab-bar {
    margin-bottom: 1.25rem;
}
.next-step-btn {
    margin-top: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🩺 企业诊断辅导</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">填写或加载企业画像，运行政策诊断，查看报告与培育路线图。</div>', unsafe_allow_html=True)

ENTERPRISE_FILE = "data/enterprise.json"
DIAGNOSIS_FILE = "output/diagnosis_result.json"

# 初始化 session_state
if "enterprise_profile" not in st.session_state:
    if os.path.exists(ENTERPRISE_FILE):
        st.session_state["enterprise_profile"] = load_json(ENTERPRISE_FILE)
    else:
        st.session_state["enterprise_profile"] = {}

if "diagnosis_result" not in st.session_state and os.path.exists(DIAGNOSIS_FILE):
    try:
        with open(DIAGNOSIS_FILE, "r", encoding="utf-8") as f:
            st.session_state["diagnosis_result"] = json.load(f)
    except Exception:
        st.session_state["diagnosis_result"] = None

TABS = [
    {"key": "profile", "label": "🏢 企业画像"},
    {"key": "diagnosis", "label": "🔍 政策诊断"},
    {"key": "report", "label": "📋 诊断报告"},
    {"key": "roadmap", "label": "🌱 培育路线图"},
]

if "enterprise_active_tab" not in st.session_state:
    st.session_state["enterprise_active_tab"] = "profile"

active_tab = st.session_state["enterprise_active_tab"]


def _set_tab(tab_key: str):
    st.session_state["enterprise_active_tab"] = tab_key


def _render_tab_bar():
    """渲染顶部可点击标签栏"""
    cols = st.columns(len(TABS))
    for col, tab in zip(cols, TABS):
        with col:
            btn_type = "primary" if tab["key"] == active_tab else "secondary"
            st.button(
                tab["label"],
                key=f"tab_btn_{tab['key']}",
                type=btn_type,
                use_container_width=True,
                on_click=_set_tab,
                args=(tab["key"],),
            )


_render_tab_bar()


# ========== 企业画像 ==========
if active_tab == "profile":
    st.markdown('<div class="section-title" style="margin-top:0">🏢 企业画像录入</div>', unsafe_allow_html=True)

    ep = st.session_state["enterprise_profile"]

    with st.form("enterprise_profile_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("企业名称", value=ep.get("name", ""))
            industry = st.text_input("所属行业", value=ep.get("industry", "新能源汽车"))
            province = st.text_input("省份", value=ep.get("province", "安徽省"))
            founded_year = st.number_input("成立年份", min_value=1900, max_value=2100, value=int(ep.get("founded_year", 2015)))
            employees = st.number_input("员工人数", min_value=0, value=int(ep.get("employees", 0)))
            revenue = st.number_input("上年度营收（万元）", min_value=0.0, value=float(ep.get("revenue", 0)))
            rd_investment = st.number_input("研发投入（万元）", min_value=0.0, value=float(ep.get("rd_investment") or 0))
            invention_patents = st.number_input("发明专利数量", min_value=0, value=int(ep.get("invention_patents", 0)))
        with c2:
            sub_industry = st.text_input("细分行业", value=ep.get("sub_industry", "动力电池"))
            scale_options = ["小型企业", "中型企业", "大型企业", "规模以上"]
            current_scale = ep.get("scale", "小型企业")
            scale_index = scale_options.index(current_scale) if current_scale in scale_options else 0
            scale = st.selectbox("企业规模", scale_options, index=scale_index)
            city = st.text_input("城市", value=ep.get("city", "合肥市"))
            region = st.text_input("所在地区", value=ep.get("region", "安徽省合肥市高新区"))
            profit = st.number_input("上年度利润（万元）", min_value=0.0, value=float(ep.get("profit", 0)))
            rd_ratio = st.number_input("研发投入占比", min_value=0.0, max_value=1.0, value=float(ep.get("rd_ratio", 0.0)), step=0.01, format="%.2f")
            rd_team_size = st.number_input("研发人员数量", min_value=0, value=int(ep.get("rd_team_size") or 0))
            utility_models = st.number_input("实用新型专利数量", min_value=0, value=int(ep.get("utility_models", 0)))
        with c3:
            core_product = st.text_input("核心产品", value=ep.get("core_product", ""))
            rd_team_ratio = st.number_input("研发人员占比", min_value=0.0, max_value=1.0, value=float(ep.get("rd_team_ratio", 0.0)), step=0.01, format="%.2f")
            high_tech_income_ratio = st.number_input("高新技术产品收入占比", min_value=0.0, max_value=1.0, value=float(ep.get("high_tech_income_ratio", 0.0)), step=0.01, format="%.2f")
            software_copyrights = st.number_input("软件著作权数量", min_value=0, value=int(ep.get("software_copyrights", 0)))
            trademarks = st.number_input("商标数量", min_value=0, value=int(ep.get("trademarks", 0)))
            is_high_tech_enterprise = st.checkbox("国家高新技术企业", value=ep.get("is_high_tech_enterprise", False))
            is_high_tech_field = st.checkbox("属于高新技术领域", value=ep.get("is_high_tech_field", True))
            market_share_proof = st.checkbox("有市场占有率证明", value=ep.get("market_share_proof", False))
            rd_accounting_system = st.checkbox("建立研发准备金制度", value=ep.get("rd_accounting_system", False))
            has_major_accident = st.checkbox("近三年有重大事故", value=ep.get("has_major_accident", False))

        qualification_options = [
            "国家高新技术企业", "国家级专精特新小巨人", "安徽省专精特新中小企业",
            "科技型中小企业", "创新型中小企业", "ISO9001", "ISO13485",
            "CE认证", "医疗器械生产许可证", "医疗器械产品注册证"
        ]
        default_qualifications = ep.get("qualifications", []) or []
        if not isinstance(default_qualifications, list):
            default_qualifications = []
        default_qualifications = [q for q in default_qualifications if q in qualification_options]

        qualifications = st.multiselect(
            "已获资质",
            options=qualification_options,
            default=default_qualifications,
        )

        submitted = st.form_submit_button("💾 保存企业画像", type="primary", use_container_width=True)

    if submitted:
        years_in_operation = 2026 - founded_year
        years_in_segment = ep.get("years_in_segment", years_in_operation)
        profile = {
            "name": name,
            "industry": industry,
            "sub_industry": sub_industry,
            "province": province,
            "city": city,
            "region": region,
            "founded_year": founded_year,
            "scale": scale,
            "employees": employees,
            "revenue": revenue,
            "profit": profit,
            "rd_investment": rd_investment,
            "rd_ratio": rd_ratio,
            "rd_team_size": rd_team_size,
            "rd_team_ratio": rd_team_ratio,
            "invention_patents": invention_patents,
            "utility_models": utility_models,
            "software_copyrights": software_copyrights,
            "trademarks": trademarks,
            "qualifications": qualifications,
            "is_high_tech_enterprise": is_high_tech_enterprise,
            "is_high_tech_field": is_high_tech_field,
            "high_tech_income_ratio": high_tech_income_ratio,
            "has_major_accident": has_major_accident,
            "market_share_proof": market_share_proof,
            "rd_accounting_system": rd_accounting_system,
            "years_in_operation": years_in_operation,
            "years_in_segment": years_in_segment,
            "core_product": core_product,
        }
        profile["capability_scores"] = calculate_dimension_scores(profile)
        os.makedirs("data", exist_ok=True)
        with open(ENTERPRISE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
        st.session_state["enterprise_profile"] = profile
        st.success("✅ 企业画像已保存")
        st.info("请点击下方「下一步」按钮，进入政策诊断。")
        st.button(
            "下一步：运行政策诊断 →",
            type="primary",
            use_container_width=True,
            on_click=_set_tab,
            args=("diagnosis",),
        )


# ========== 政策诊断 ==========
elif active_tab == "diagnosis":
    st.markdown('<div class="section-title" style="margin-top:0">🔍 政策诊断</div>', unsafe_allow_html=True)

    if not os.path.exists(ENTERPRISE_FILE):
        st.warning("⚠️ 请先填写并保存企业画像。")
        st.button(
            "前往企业画像",
            type="primary",
            use_container_width=True,
            on_click=_set_tab,
            args=("profile",),
        )
        st.stop()

    enterprise = st.session_state["enterprise_profile"]
    st.markdown(f"当前企业：**{enterprise.get('name', '未命名')}** | 行业：{enterprise.get('industry', '')} - {enterprise.get('sub_industry', '')} | 地区：{enterprise.get('region', '')}")

    llm_config = get_api_config()
    use_demo_default = llm_config["use_demo"]
    use_demo = st.toggle("使用演示模式（无需 API Key）", value=use_demo_default)

    if st.button("🚀 运行政策诊断", type="primary", use_container_width=True):
        with st.status("正在加载政策库并运行诊断...", expanded=True) as status:
            policies = load_json("data/policies.json")
            status.update(label=f"已加载 {len(policies)} 条政策，正在匹配...")
            result = run_enhanced_diagnosis(
                enterprise=enterprise,
                policies=policies,
                use_demo=use_demo,
                max_policies_for_soft_score=5,
            )
            os.makedirs("output", exist_ok=True)
            with open(DIAGNOSIS_FILE, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            st.session_state["diagnosis_result"] = result
            status.update(label="诊断完成", state="complete")
        st.success("✅ 诊断完成，请选择下一步：")
        c1, c2 = st.columns(2)
        with c1:
            st.button(
                "查看诊断报告",
                type="primary",
                use_container_width=True,
                on_click=_set_tab,
                args=("report",),
            )
        with c2:
            st.button(
                "查看培育路线图",
                type="primary",
                use_container_width=True,
                on_click=_set_tab,
                args=("roadmap",),
            )

    result = st.session_state.get("diagnosis_result")
    if not result:
        st.info("💡 点击上方按钮运行诊断。")
        st.stop()

    metrics = compute_dashboard_metrics(result)
    st.markdown("#### 诊断结果概览")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f'''<div class="metric-card"><div class="metric-value">{metrics["total"]}</div><div class="metric-label">匹配政策数</div></div>''', unsafe_allow_html=True)
    with m2:
        st.markdown(f'''<div class="metric-card"><div class="metric-value status-immediate">{metrics["immediate"]}</div><div class="metric-label">立即申报</div></div>''', unsafe_allow_html=True)
    with m3:
        st.markdown(f'''<div class="metric-card"><div class="metric-value status-cultivate">{metrics["cultivate"]}</div><div class="metric-label">培育申报</div></div>''', unsafe_allow_html=True)
    with m4:
        st.markdown(f'''<div class="metric-card"><div class="metric-value status-watch">{metrics["watch"]}</div><div class="metric-label">持续关注</div></div>''', unsafe_allow_html=True)
    with m5:
        st.markdown(f'''<div class="metric-card"><div class="metric-value status-unsuitable">{metrics["unsuitable"]}</div><div class="metric-label">暂不适合</div></div>''', unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 详细诊断结果")

    sort_by = st.selectbox("排序方式", ["行动优先级", "综合分数降序", "截止日由近到远", "政策优先级"], index=0)
    sorted_results = sort_results_for_display(result.get("results", []), sort_by)

    policy_map = {p["policy_id"]: p for p in load_json("data/policies.json")}

    for r in sorted_results:
        diag = r.get("diagnosis", "")
        color_class = {
            "立即申报": "status-immediate",
            "培育申报": "status-cultivate",
            "持续关注": "status-watch",
            "暂不适合": "status-unsuitable",
        }.get(diag, "")
        score = r.get("combined_score", r.get("match_score", 0))
        with st.expander(f"{r.get('policy_name', '')}  ·  {diag}  ·  {score}分", expanded=False):
            c_left, c_right = st.columns([2, 1])
            with c_left:
                st.markdown(f"**政策层级**：{r.get('level', '')}")
                st.markdown(f"**政策类别**：{r.get('category', '')}")
                st.markdown(f"**扶持内容**：{r.get('benefit', '')}")
                st.markdown(f"**申报截止**：{r.get('deadline', '')}")
                st.markdown(f"**诊断理由**：{r.get('reason', '')}")
                if r.get("failed"):
                    st.markdown("**不满足条件**：")
                    for item in r["failed"]:
                        st.markdown(f"- {item}")
                if r.get("unknown"):
                    st.markdown("**缺失数据**：")
                    for item in r["unknown"]:
                        st.markdown(f"- {item}")
            with c_right:
                st.markdown(f"**综合分数**：{score} 分")
                if "hard_score" in r:
                    st.markdown(f"**硬条件**：{r.get('hard_score')} 分")
                if r.get("soft_score") is not None:
                    st.markdown(f"**软条件**：{r.get('soft_score')} 分（置信度：{r.get('confidence', '未知')}）")
                if r.get("soft_assessment") and r.get("soft_assessment") != "未进行软条件评估":
                    st.markdown(f"**软条件评估**：{r['soft_assessment']}")

            if diag in ["立即申报", "培育申报"]:
                if st.button(f"📝 生成《{r['policy_name']}》申报大纲", key=f"outline_{r['policy_id']}"):
                    policy = policy_map.get(r["policy_id"], {})
                    llm_cfg = get_api_config()
                    outline = generate_material_outline(
                        enterprise=enterprise,
                        policy=policy,
                        hard_result=r,
                        soft_result={
                            "soft_score": r.get("soft_score"),
                            "assessment": r.get("soft_assessment", ""),
                            "strengths": r.get("strengths", []),
                            "weaknesses": r.get("weaknesses", []),
                            "cultivation_suggestions": r.get("cultivation_suggestions", []),
                        },
                        provider=llm_cfg["provider"],
                        api_key=llm_cfg["api_key"],
                        use_demo=llm_cfg["use_demo"] or use_demo,
                    )
                    r["material_outline"] = outline
                    # 回写结果文件
                    with open(DIAGNOSIS_FILE, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    st.success(f"已生成《{r['policy_name']}》申报大纲")
                    st.markdown(f"**申报可行性**：{outline.get('applicability', '')}")
                    if outline.get("outline"):
                        for section in outline["outline"]:
                            st.markdown(f"- **{section.get('section', '')}**：{'; '.join(section.get('content', []))}")


# ========== 诊断报告 ==========
elif active_tab == "report":
    st.markdown('<div class="section-title" style="margin-top:0">📋 诊断报告</div>', unsafe_allow_html=True)

    result = st.session_state.get("diagnosis_result")
    if not result:
        st.warning("⚠️ 请先运行政策诊断。")
        st.button(
            "前往政策诊断",
            type="primary",
            use_container_width=True,
            on_click=_set_tab,
            args=("diagnosis",),
        )
        st.stop()

    enterprise = st.session_state["enterprise_profile"]
    capability_scores = enterprise.get("capability_scores") or calculate_dimension_scores(enterprise)

    # 雷达图
    fig_radar = build_radar_chart(capability_scores, title=f"{enterprise.get('name', '企业')} 综合能力雷达图")
    st.plotly_chart(fig_radar, use_container_width=True, key="enterprise_radar")

    # TOP3
    top3 = select_top3_policies(result.get("results", []))
    st.markdown("#### 🎯 TOP3 推荐政策")
    for p in top3:
        st.markdown(f"""
        <div class="result-card">
            <div style="font-weight:600">{p['rank']}. {p['policy_name']}  ·  {p['diagnosis']}  ·  {p['combined_score']}分</div>
            <div style="color:var(--apple-muted);font-size:0.85rem;margin:0.25rem 0">{p['timeline_advice']}</div>
            <div>扶持内容：{p['benefit']}</div>
        </div>
        """, unsafe_allow_html=True)

    # 导出
    st.markdown("#### 📥 报告导出")
    radar_bytes = None
    try:
        radar_bytes = fig_to_image_bytes(fig_radar, format="png")
    except Exception:
        radar_bytes = None

    md_report = build_markdown_report(result)
    word_bytes = build_word_report(result, capability_scores=capability_scores, radar_image_bytes=radar_bytes)
    pdf_bytes = build_pdf_report(result, capability_scores=capability_scores, radar_image_bytes=radar_bytes)

    e1, e2, e3 = st.columns(3)
    with e1:
        st.download_button("下载 Markdown", md_report, file_name=f"{enterprise.get('name', '企业')}_政策诊断报告.md", mime="text/markdown", use_container_width=True)
    with e2:
        st.download_button("下载 Word", word_bytes, file_name=f"{enterprise.get('name', '企业')}_政策诊断报告.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with e3:
        st.download_button("下载 PDF", pdf_bytes, file_name=f"{enterprise.get('name', '企业')}_政策诊断报告.pdf", mime="application/pdf", use_container_width=True)


# ========== 培育路线图 ==========
elif active_tab == "roadmap":
    st.markdown('<div class="section-title" style="margin-top:0">🌱 培育路线图</div>', unsafe_allow_html=True)

    result = st.session_state.get("diagnosis_result")
    if not result:
        st.warning("⚠️ 请先运行政策诊断。")
        st.button(
            "前往政策诊断",
            type="primary",
            use_container_width=True,
            on_click=_set_tab,
            args=("diagnosis",),
        )
        st.stop()

    if "roadmap" not in st.session_state:
        roadmap = generate_enterprise_roadmap(result, focus_diagnoses=["培育申报", "暂不适合"], top_n=5)
        save_roadmap(roadmap)
        st.session_state["roadmap"] = roadmap

    roadmap = st.session_state["roadmap"]
    summary = roadmap.get("summary", {})

    st.markdown(f"覆盖政策数：**{summary.get('target_policies', 0)}** 条 · 培育动作总数：**{summary.get('total_actions', 0)}** 项")

    for phase in PHASE_ORDER:
        actions = roadmap.get("phased_actions", {}).get(phase, [])
        if not actions:
            continue
        with st.expander(f"{PHASE_LABELS[phase]}（{len(actions)} 项）", expanded=True):
            for action in actions:
                st.markdown(f"""
                <div class="phase-card">
                    <div class="action-title">{action.get('title', '')}</div>
                    <div class="action-meta">负责方：{action.get('owner', '')}  |  难度：{action.get('difficulty', '')}  |  预计：{action.get('estimated_time', '')} / {action.get('estimated_cost', '')}</div>
                    <div>{action.get('description', '')}</div>
                    {'<div style="margin-top:0.5rem;color:var(--apple-muted);font-size:0.85rem">关联政策：' + '、'.join(action.get('related_policies', [])) + '</div>' if action.get('related_policies') else ''}
                </div>
                """, unsafe_allow_html=True)

    md_roadmap = build_roadmap_markdown(roadmap)
    st.download_button("下载培育路线图 Markdown", md_roadmap, file_name=f"{roadmap.get('enterprise_name', '企业')}_政策培育路线图.md", mime="text/markdown", use_container_width=True)

st.info("💡 提示：本页面复用了原有「企业政策诊断辅导」能力，可对单个企业进行画像、诊断、报告导出与培育路线规划。")
