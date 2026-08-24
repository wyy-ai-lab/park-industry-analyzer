import pandas as pd
import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.park_metrics import load_park_enterprises, compute_metrics
from engine.chain_position import SEGMENT_LAYER_MAP, classify_segment_strength
from engine.park_charts import build_segment_strength_chart

st.set_page_config(
    page_title="产业链图谱 - 园区产业分析智能体",
    page_icon="🕸️",
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
.metric-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow-sm);
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--apple-text);
    letter-spacing: -0.02em;
}
.metric-label {
    font-size: 0.85rem;
    color: var(--apple-muted);
    margin-top: 0.25rem;
}
.segment-list {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1rem 1.25rem;
    box-shadow: var(--shadow-sm);
    margin-bottom: 0.75rem;
}
.segment-list-title {
    font-weight: 600;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.segment-list-items {
    font-size: 0.92rem;
    color: var(--apple-text);
    line-height: 1.6;
}
.status-strong { color: #0071e3; }
.status-normal { color: #34c759; }
.status-weak { color: #ff9500; }
.status-missing { color: #ff3b30; }
.risk-card {
    background: rgba(255, 59, 48, 0.08);
    border: 1px solid rgba(255, 59, 48, 0.3);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    box-shadow: var(--shadow-sm);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🕸️ 产业链图谱</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">识别产业链强弱环节、缺失环节与断链风险。</div>', unsafe_allow_html=True)

# 加载数据
data = load_park_enterprises()
if not data or not data.get("enterprises"):
    st.warning("⚠️ 未找到园区企业数据，请确认 `data/park_enterprises.json` 存在。")
    st.stop()

metrics = compute_metrics(data)
segment_dist = metrics["segment_distribution"]
segment_strength = metrics["segment_strength"]

# 计算每个环节的状态
segment_status = {}
for seg, info in segment_dist.items():
    segment_status[seg] = classify_segment_strength(seg, info["count"], info["revenue"])
for seg in segment_strength["missing"]:
    segment_status[seg] = "缺失"

# 核心指标
st.markdown('<div class="section-title">📊 产业链核心指标</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{metrics['completeness_score']}分</div>
        <div class="metric-label">产业链完整度</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{metrics['local_support_rate']}%</div>
        <div class="metric-label">本地配套率</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    covered = len(segment_dist)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{covered}/{len(SEGMENT_LAYER_MAP)}</div>
        <div class="metric-label">已布局环节</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    risk_count = len(segment_strength["risk"])
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {'#ff3b30' if risk_count > 0 else 'var(--apple-text)'};">{risk_count}个</div>
        <div class="metric-label">风险环节</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# 产业链环节布局图
st.markdown('<div class="section-title">🕸️ 产业链环节布局</div>', unsafe_allow_html=True)
fig_segment = build_segment_strength_chart(segment_dist, segment_status)
st.plotly_chart(fig_segment, use_container_width=True, key="chain_segment")

# 环节明细表
st.markdown("**环节明细**")
segment_rows = []
for seg, info in segment_dist.items():
    segment_rows.append({
        "环节": seg,
        "层级": info["chain_position"],
        "企业数": info["count"],
        "年产值（亿元）": round(info["revenue"], 2),
        "状态": segment_status.get(seg, "正常"),
        "代表企业": "、".join(info["enterprises"][:3]),
    })
segment_df = pd.DataFrame(segment_rows)
# 按层级排序
layer_order = {"上游": 0, "中游": 1, "下游": 2}
segment_df["排序"] = segment_df["层级"].map(layer_order)
segment_df = segment_df.sort_values("排序").drop(columns=["排序"])
st.dataframe(segment_df, use_container_width=True, hide_index=True)

st.divider()

# 强弱缺失列表
st.markdown('<div class="section-title">⚖️ 产业链强弱分析</div>', unsafe_allow_html=True)
list_col1, list_col2 = st.columns(2)
with list_col1:
    strong_items = segment_strength["strong"]
    weak_items = segment_strength["weak"]
    st.markdown(f"""
    <div class="segment-list">
        <div class="segment-list-title">
            <span class="status-strong">●</span> 强势环节（{len(strong_items)}）
        </div>
        <div class="segment-list-items">{"、".join(strong_items) if strong_items else "无"}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="segment-list">
        <div class="segment-list-title">
            <span class="status-weak">●</span> 薄弱环节（{len(weak_items)}）
        </div>
        <div class="segment-list-items">{"、".join(weak_items) if weak_items else "无"}</div>
    </div>
    """, unsafe_allow_html=True)

with list_col2:
    missing_items = segment_strength["missing"]
    risk_items = segment_strength["risk"]
    st.markdown(f"""
    <div class="segment-list">
        <div class="segment-list-title">
            <span class="status-missing">●</span> 缺失环节（{len(missing_items)}）
        </div>
        <div class="segment-list-items">{"、".join(missing_items) if missing_items else "无"}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="risk-card">
        <div class="segment-list-title" style="color: #ff3b30;">
            ⚠️ 断链风险环节（{len(risk_items)}）
        </div>
        <div class="segment-list-items">{"、".join(risk_items) if risk_items else "无"}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# 补链建议
st.markdown('<div class="section-title">💡 补链建议</div>', unsafe_allow_html=True)
if missing_items:
    st.markdown(f"- **优先招引**：{'、'.join(missing_items)} 等缺失环节企业，补齐上游原材料与核心器件短板。")
if weak_items:
    st.markdown(f"- **重点培育**：{'、'.join(weak_items)} 等薄弱环节，支持现有企业技术升级与产能扩张。")
st.markdown("- **强化配套**：围绕动力电池、整车制造等链主企业，提升本地供应商配套比例，降低对外依赖。")
st.markdown("- **风险预警**：关注车规级芯片、高精度传感器等关键环节的供应链安全，建立重点企业监测机制。")

st.info("💡 提示：产业链完整度 = 已布局环节数 / 参考环节总数；本地配套率 ≈ 有本地供应商的企业占比。")
