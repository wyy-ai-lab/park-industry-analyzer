"""
访问控制、部署模式与数据安全提示
================================
一套代码支持两种部署形态（ Secrets 不同即可）：

- demo（公开演示版，默认）：无口令，客户打开即用；建议 Cloud Secrets
  配置 LLM Key，让访客体验完整智能梳理链路。
- internal（内部使用版）：配置 APP_PASSWORD 启用口令门 + 内部知识库；
  未配置 APP_PASSWORD 时侧边栏会警告"内部版未加锁"。

部署模式判定：显式 APP_MODE=demo/internal，或按"是否配置 APP_PASSWORD"推断。

- 每个页面顶部调用 require_auth()，直接访问子页面 URL 也会被拦下
  （仅当配置了 APP_PASSWORD 时启用）。
- render_auth_controls() 在侧边栏显示部署模式徽标、登录状态/退出按钮，
  以及「LLM 模式材料外发」的数据安全提示。
"""

import hmac

import streamlit as st

from .park_llm import _read_config


def _password() -> str:
    return (_read_config("APP_PASSWORD") or "").strip()


def get_app_mode() -> str:
    """返回部署模式：demo（公开演示）/ internal（内部使用）。"""
    mode = (_read_config("APP_MODE") or "").strip().lower()
    if mode in ("demo", "internal"):
        return mode
    return "internal" if _password() else "demo"


def is_auth_enabled() -> bool:
    return bool(_password())


def is_authed() -> bool:
    return bool(st.session_state.get("_app_authed", False))


def require_auth() -> None:
    """页面级口令门：未登录时渲染登录框并 st.stop()。app.py 与所有 pages 均需调用。

    仅当配置了 APP_PASSWORD 时启用；演示版（demo 模式）默认无口令。
    """
    pwd = _password()
    if not pwd:
        # 内部版未配置口令：警告管理员（每个 session 提示一次），演示版静默放行
        if get_app_mode() == "internal" and \
                not st.session_state.pop("_auth_off_notice_shown", False):
            st.session_state["_auth_off_notice_shown"] = True
            st.sidebar.warning("🔓 内部版未设置 APP_PASSWORD：任何知道链接的人都能访问，"
                               "请在 Secrets/环境变量中配置访问口令。")
        return

    if is_authed():
        return

    st.markdown("## 🔐 园区产业分析智能体")
    st.caption("内部系统 · 请输入访问口令")
    with st.form("app_login"):
        entered = st.text_input("访问口令", type="password")
        submitted = st.form_submit_button("进入", use_container_width=True)
    if submitted:
        if hmac.compare_digest(entered.strip(), pwd):
            st.session_state["_app_authed"] = True
            st.rerun()
        else:
            st.error("口令不正确，请重试")
    st.stop()


def render_auth_controls() -> None:
    """侧边栏：部署模式徽标 + 登录状态/退出按钮 + 数据出域安全提示。"""
    # 部署模式徽标
    if get_app_mode() == "internal":
        st.sidebar.markdown("🔒 **内部版** · 凭口令访问")
    else:
        st.sidebar.markdown("🎬 **演示版** · 对外演示，请勿录入真实敏感材料")

    if is_auth_enabled():
        if is_authed():
            st.sidebar.success("已登录")
            if st.sidebar.button("退出登录", use_container_width=True):
                st.session_state["_app_authed"] = False
                st.rerun()
        else:
            st.sidebar.warning("🔐 未登录")

    # 数据出域提示：LLM 模式开启时，材料文本会发送至所配置的 LLM 服务商
    st.sidebar.divider()
    st.sidebar.caption(
        "🛡️ 智能模式下材料文本会发送至模型服务商，请勿粘贴涉密内容；"
        "「🔒 敏感材料本地处理」开启后零外发。"
    )
