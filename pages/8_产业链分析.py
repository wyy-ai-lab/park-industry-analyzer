"""
产业链分析
============
模块二：产业分类 + 上中下游环节图谱 + 优势/薄弱/缺失环节诊断。
数据来自「园区产业概况」运行的梳理结果。
"""

import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.auth import require_auth
from engine.ia_sections import (
    inject_ia_css, render_ia_header, get_result,
    render_classification, render_chain_analysis,
)

st.set_page_config(page_title="产业链分析", page_icon="🧬", layout="wide")
inject_apple_theme()
inject_ia_css()
require_auth()
st.session_state["_page_id"] = "chain"

result = get_result()
render_ia_header(
    "🧬 产业链分析",
    "对园区产业进行分类，描述产业链条上中下游布局，识别优势、薄弱与缺失环节。",
    result,
)

if result:
    render_classification(result)
    render_chain_analysis(result)
    st.markdown('<div style="font-size:0.85rem;color:var(--td-muted);margin-top:1rem">'
                '下一步：'
                '<a href="产业发展建议" style="margin-right:0.9rem">💡 产业发展建议</a>'
                '<a href="产业招商推荐">🎯 产业招商推荐</a></div>',
                unsafe_allow_html=True)
