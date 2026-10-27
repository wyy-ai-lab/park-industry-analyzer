"""
产业发展建议
============
模块三：针对优势、薄弱与缺失环节，生成强链 / 补链 / 延链发展路径。
数据来自「园区产业概况」运行的梳理结果。
"""

import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.auth import require_auth
from engine.ia_sections import (
    inject_ia_css, render_ia_header, get_result, render_paths_section,
)

st.set_page_config(page_title="产业发展建议", page_icon="💡", layout="wide")
inject_apple_theme()
inject_ia_css()
require_auth()
st.session_state["_page_id"] = "advice"

result = get_result()
render_ia_header(
    "💡 产业发展建议",
    "针对产业链分析识别的优势、薄弱与缺失环节，提出对应的产业发展路径。",
    result,
)

if result:
    render_paths_section(result)
    st.markdown('<div style="font-size:0.85rem;color:var(--td-muted);margin-top:1rem">'
                '下一步：<a href="产业招商推荐">🎯 产业招商推荐</a></div>',
                unsafe_allow_html=True)
