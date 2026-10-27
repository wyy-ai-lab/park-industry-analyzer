"""
访问控制与数据安全提示
======================
内部部署用简易口令门：

- 在 `.streamlit/secrets.toml` 或环境变量中配置 APP_PASSWORD 即启用；
  未配置时应用完全放行（并给出一次性提示，避免误以为已加锁）。
- 每个页面顶部调用 require_auth()，直接访问子页面 URL 也会被拦下。
- render_auth_controls() 在侧边栏显示登录状态与退出按钮，以及
  「LLM 模式材料外发」的数据安全提示。
"""

import hmac

import streamlit as st

from .park_llm import _read_config


def _password() -> str:
    return (_read_config("APP_PASSWORD") or "").strip()


def is_auth_enabled() -> bool:
    return bool(_password())


def is_authed() -> bool:
    return bool(st.session_state.get("_app_authed", False))


def require_auth() -> None:
    """页面级口令门：未登录时渲染登录框并 st.stop()。app.py 与所有 pages 均需调用。"""
    pwd = _password()
    if not pwd:
        # 未配置口令：功能放行，但提醒管理员（每个 session 提示一次）
        if not st.session_state.pop("_auth_off_notice_shown", False):
            st.session_state["_auth_off_notice_shown"] = True
            st.sidebar.info("🔓 访问控制未启用：在 Secrets/环境变量中设置 APP_PASSWORD 后，"
                            "内部人员需凭口令进入。")
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
    """侧边栏：登录状态 / 退出按钮 + 数据出域安全提示。"""
    if is_auth_enabled():
        if is_authed():
            st.sidebar.success("🔒 已登录（内部访问）")
            if st.sidebar.button("退出登录", use_container_width=True):
                st.session_state["_app_authed"] = False
                st.rerun()
        else:
            st.sidebar.warning("🔐 未登录")

    # 数据出域提示：LLM 模式开启时，材料文本会发送至所配置的 LLM 服务商
    st.sidebar.divider()
    st.sidebar.caption(
        "🛡️ **数据安全提示**\n\n"
        "· LLM 智能模式下，材料文本会发送至所配置的模型服务商"
        "（Anthropic / OpenAI / 国内模型）\n\n"
        "· 请勿粘贴涉密的企业经营数据、未公开政策文件\n\n"
        "· 模板/演示模式全部在本地处理，不发生任何外发"
    )
