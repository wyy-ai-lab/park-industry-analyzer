import pandas as pd
import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.park_metrics import load_park_enterprises
from engine.industry_classifier import classify

st.set_page_config(
    page_title="企业透视 - 政策-产业-企业智能体",
    page_icon="🔍",
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
.tag {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 500;
    margin-right: 0.35rem;
    margin-bottom: 0.2rem;
}
.tag-blue { background: rgba(0, 113, 227, 0.12); color: #0071e3; }
.tag-green { background: rgba(52, 199, 89, 0.12); color: #34c759; }
.tag-orange { background: rgba(255, 149, 0, 0.12); color: #ff9500; }
.tag-purple { background: rgba(175, 82, 222, 0.12); color: #af52de; }
.tag-gray { background: #f2f2f7; color: #6e6e73; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🔍 企业透视</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">搜索、筛选、下钻园区企业，一键进入单个企业诊断辅导。</div>', unsafe_allow_html=True)

# 加载数据
data = load_park_enterprises()
if not data or not data.get("enterprises"):
    if st.session_state.get("use_demo_data", True):
        st.warning("⚠️ 未找到园区企业数据，请确认 `data/park_enterprises.json` 存在。")
    else:
        st.warning("📦 演示数据已关闭，当前为「未接入数据」状态。返回首页打开左侧开关「载入演示数据」即可查看演示内容。")
    st.stop()

enterprises = data["enterprises"]

# 创新评分（简单规则）
def innovation_score(e):
    score = 0
    score += min(e.get("patents", 0) / 10, 30)
    score += min(e.get("invention_patents", 0) / 5, 20)
    score += e.get("rd_investment_ratio", 0) * 200
    score += min(e.get("rd_personnel", 0) / 5, 20)
    score += e.get("master_doctor_ratio", 0) * 20
    score += e.get("leading_talents", 0) * 3
    score += 10 if e.get("high_tech_enterprise") else 0
    score += 10 if e.get("little_giant") else 0
    return min(round(score), 100)

# 构建 DataFrame
rows = []
for e in enterprises:
    tags = classify(name=e.get("name", ""), products=e.get("main_products", ""))
    rows.append({
        "企业ID": e.get("enterprise_id", ""),
        "企业名称": e.get("name", ""),
        "产业领域": e.get("sub_industry", ""),
        "细分领域": e.get("niche", ""),
        "产业链位置": e.get("chain_position", ""),
        "企业角色": e.get("enterprise_role", ""),
        "年产值（亿元）": e.get("annual_revenue", 0),
        "员工数": e.get("employees", 0),
        "研发投入占比": f"{e.get('rd_investment_ratio', 0) * 100:.1f}%",
        "专利数": e.get("patents", 0),
        "创新评分": innovation_score(e),
        "标签": "、".join(tags["niche_tags"]),
        "是否高企": "是" if e.get("high_tech_enterprise") else "否",
        "是否小巨人": "是" if e.get("little_giant") else "否",
    })

df = pd.DataFrame(rows)

# 筛选栏
st.markdown('<div class="section-title">🔎 筛选企业</div>', unsafe_allow_html=True)
f1, f2, f3, f4 = st.columns(4)
with f1:
    search_name = st.text_input("企业名称关键词", "")
with f2:
    sub_options = sorted(df["产业领域"].unique().tolist())
    selected_subs = st.multiselect("产业领域", sub_options, default=sub_options)
with f3:
    role_options = sorted(df["企业角色"].unique().tolist())
    selected_roles = st.multiselect("企业角色", role_options, default=role_options)
with f4:
    chain_options = sorted(df["产业链位置"].unique().tolist())
    selected_chains = st.multiselect("产业链位置", chain_options, default=chain_options)

# 应用筛选
filtered = df.copy()
if search_name:
    filtered = filtered[filtered["企业名称"].str.contains(search_name, na=False)]
if selected_subs:
    filtered = filtered[filtered["产业领域"].isin(selected_subs)]
if selected_roles:
    filtered = filtered[filtered["企业角色"].isin(selected_roles)]
if selected_chains:
    filtered = filtered[filtered["产业链位置"].isin(selected_chains)]

st.markdown(f"共筛选出 **{len(filtered)}** / {len(df)} 家企业")

# 表格展示
st.markdown('<div class="section-title">📋 企业列表</div>', unsafe_allow_html=True)

# 使用 data_editor 或 dataframe 展示
st.dataframe(
    filtered[[
        "企业ID", "企业名称", "产业领域", "细分领域", "产业链位置",
        "企业角色", "年产值（亿元）", "员工数", "研发投入占比", "专利数", "创新评分"
    ]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "年产值（亿元）": st.column_config.NumberColumn(format="%.2f"),
        "创新评分": st.column_config.ProgressColumn(min_value=0, max_value=100),
    },
)

# 企业详情与诊断入口
st.divider()
st.markdown('<div class="section-title">🏢 企业详情与诊断入口</div>', unsafe_allow_html=True)

selected_id = st.selectbox(
    "选择企业查看详情",
    options=filtered["企业ID"].tolist(),
    format_func=lambda x: f"{x} - {filtered[filtered['企业ID'] == x]['企业名称'].values[0]}",
)

if selected_id:
    selected_enterprise = next(e for e in enterprises if e.get("enterprise_id") == selected_id)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"**企业名称**：{selected_enterprise.get('name', '')}")
        st.markdown(f"**产业领域**：{selected_enterprise.get('sub_industry', '')} / {selected_enterprise.get('niche', '')}")
        st.markdown(f"**产业链位置**：{selected_enterprise.get('chain_position', '')}（{selected_enterprise.get('chain_position_detail', '')}）")
        st.markdown(f"**企业角色**：{selected_enterprise.get('enterprise_role', '')}")
        st.markdown(f"**成立年份**：{selected_enterprise.get('founded_year', '')}")
        st.markdown(f"**员工数**：{selected_enterprise.get('employees', 0)} 人")
        st.markdown(f"**年产值**：{selected_enterprise.get('annual_revenue', 0):.2f} 亿元")
        st.markdown(f"**研发投入占比**：{selected_enterprise.get('rd_investment_ratio', 0) * 100:.1f}%")
        st.markdown(f"**专利数**：{selected_enterprise.get('patents', 0)} 项（发明专利 {selected_enterprise.get('invention_patents', 0)} 项）")
        st.markdown(f"**核心技术**：{selected_enterprise.get('core_technology', '')}")
    with c2:
        st.markdown(f"**是否高企**：{'是' if selected_enterprise.get('high_tech_enterprise') else '否'}")
        st.markdown(f"**是否小巨人**：{'是' if selected_enterprise.get('little_giant') else '否'}")
        st.markdown(f"**硕博占比**：{selected_enterprise.get('master_doctor_ratio', 0) * 100:.1f}%")
        st.markdown(f"**领军人才**：{selected_enterprise.get('leading_talents', 0)} 人")
        st.markdown(f"**主要产品**：{selected_enterprise.get('main_products', '')}")
        if selected_enterprise.get("university_cooperation"):
            st.markdown(f"**产学研合作**：{'、'.join(selected_enterprise['university_cooperation'])}")

    # 写入 enterprise.json 用于诊断
    if st.button("🩺 进入该企业政策诊断辅导", type="primary", use_container_width=True):
        # 将园区企业数据转换为企业画像格式
        profile = {
            "name": selected_enterprise.get("name", ""),
            "industry": selected_enterprise.get("industry", "新能源汽车"),
            "sub_industry": selected_enterprise.get("sub_industry", ""),
            "province": "安徽省",
            "city": "合肥市",
            "region": "安徽省合肥市高新区",
            "founded_year": selected_enterprise.get("founded_year", 2015),
            "scale": "中型企业" if selected_enterprise.get("employees", 0) > 300 else "小型企业",
            "employees": selected_enterprise.get("employees", 0),
            "revenue": selected_enterprise.get("annual_revenue", 0) * 10000,  # 万元
            "profit": selected_enterprise.get("net_profit", 0) * 10000,  # 万元
            "rd_investment": selected_enterprise.get("annual_revenue", 0) * selected_enterprise.get("rd_investment_ratio", 0) * 10000,
            "rd_ratio": selected_enterprise.get("rd_investment_ratio", 0),
            "rd_team_size": selected_enterprise.get("rd_personnel", 0),
            "rd_team_ratio": selected_enterprise.get("rd_personnel", 0) / max(selected_enterprise.get("employees", 1), 1),
            "invention_patents": selected_enterprise.get("invention_patents", 0),
            "utility_models": max(0, selected_enterprise.get("patents", 0) - selected_enterprise.get("invention_patents", 0) - selected_enterprise.get("software_copyrights", 0)),
            "software_copyrights": selected_enterprise.get("software_copyrights", 0),
            "trademarks": 0,
            "qualifications": ["国家高新技术企业"] if selected_enterprise.get("high_tech_enterprise") else [],
            "is_high_tech_enterprise": selected_enterprise.get("high_tech_enterprise", False),
            "is_high_tech_field": True,
            "high_tech_income_ratio": 0.6,
            "rd_accounting_system": True,
            "has_major_accident": False,
            "market_share_proof": False,
            "years_in_operation": 2026 - selected_enterprise.get("founded_year", 2015),
            "years_in_segment": 2026 - selected_enterprise.get("founded_year", 2015),
            "core_product": selected_enterprise.get("main_products", ""),
        }
        import json as _json
        import os as _os
        _os.makedirs("data", exist_ok=True)
        with open("data/enterprise.json", "w", encoding="utf-8") as f:
            _json.dump(profile, f, ensure_ascii=False, indent=2)
        st.success(f"✅ 已加载 {selected_enterprise.get('name')} 的企业画像，请进入「企业诊断辅导」页面。")
        st.info("👈 点击左侧菜单「企业诊断辅导」开始诊断。")

st.info("💡 提示：选择企业后点击「进入该企业政策诊断辅导」，即可进行单企业政策诊断、报告导出与培育路线规划。")
