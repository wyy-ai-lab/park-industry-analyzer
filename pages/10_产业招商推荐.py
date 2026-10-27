"""
产业招商推荐
============
模块四：按缺失与薄弱环节梳理招商目标企业，并给出研究院 / 协会等对接资源；
支持导出完整梳理报告（Markdown / Word / PDF）。
数据来自「园区产业概况」运行的梳理结果。
"""

import streamlit as st

from engine.ui_helpers import inject_apple_theme
from engine.auth import require_auth
from engine.ia_sections import (
    inject_ia_css, render_ia_header, get_result,
    render_targets_section, render_resources_subsection, render_export_block,
)

st.set_page_config(page_title="产业招商推荐", page_icon="🎯", layout="wide")
inject_apple_theme()
inject_ia_css()
require_auth()
st.session_state["_page_id"] = "invest"

result = get_result()
render_ia_header(
    "🎯 产业招商推荐",
    "围绕补链延链方向，梳理对应上中下游环节的目标招商企业与研究院/协会资源。",
    result,
)

if result:
    render_targets_section(result)
    render_resources_subsection(result)
    render_export_block(result)
