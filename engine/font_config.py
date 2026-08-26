"""
图表/导出的中文字体配置

解决 Plotly 在 Linux/Streamlit Cloud 以及部分浏览器下中文显示为
方块（tofu）的问题。优先使用系统自带中文字体，Linux 环境自动下载并注册
Noto Sans CJK SC 字体。
"""

import os
import platform
import shutil
import subprocess
import urllib.request
from functools import lru_cache


FONT_FILENAME = "NotoSansCJKsc-Regular.otf"
NOTO_URL = (
    "https://github.com/notofonts/noto-cjk/raw/main/"
    "Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
)

# 通用中文字体回退栈：
# 覆盖 Windows / macOS / Linux / iOS / Android 常见中文字体，
# 最后回退到系统默认 sans-serif。
CHART_FONT = (
    "Noto Sans CJK SC, "
    "PingFang SC, Heiti SC, Hiragino Sans GB, "
    "Microsoft YaHei, SimHei, "
    "WenQuanYi Micro Hei, "
    "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, sans-serif"
)


def _cache_dir() -> str:
    return os.path.join(os.path.expanduser("~"), ".cache", "enterprise-policy-agent")


def _ensure_cached_font() -> str:
    """把字体缓存到用户目录，返回字体路径；失败返回空字符串。"""
    cache = _cache_dir()
    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, FONT_FILENAME)
    if os.path.exists(path) and os.path.getsize(path) > 100000:
        return path
    try:
        urllib.request.urlretrieve(NOTO_URL, path)
    except Exception:
        return ""
    return path if (os.path.exists(path) and os.path.getsize(path) > 100000) else ""


@lru_cache(maxsize=1)
def _ensure_linux_font() -> str:
    """
    Linux/Streamlit Cloud 环境下把字体安装到 ~/.local/share/fonts，
    并刷新 fontconfig 缓存，让 kaleido/Chromium 能识别。
    """
    if platform.system() != "Linux":
        return ""

    cached = _ensure_cached_font()
    if not cached:
        return ""

    local_fonts_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "fonts")
    os.makedirs(local_fonts_dir, exist_ok=True)
    target = os.path.join(local_fonts_dir, FONT_FILENAME)

    if not os.path.exists(target):
        try:
            shutil.copyfile(cached, target)
        except Exception:
            return ""

    # 刷新字体缓存；忽略错误，避免无 fc-cache 时崩溃
    try:
        subprocess.run(
            ["fc-cache", "-f", local_fonts_dir],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    return target


def ensure_cjk_font_for_export() -> None:
    """
    在 Linux 服务器/Streamlit Cloud 上预先安装中文字体，
    供 kaleido 导出图片/PDF 使用。
    """
    if platform.system() == "Linux":
        _ensure_linux_font()


def get_chart_font_family() -> str:
    """
    返回 Plotly 图表使用的中文字体 family 列表。
    调用时会尝试在 Linux 环境下预装字体。
    """
    ensure_cjk_font_for_export()
    return CHART_FONT


def get_pdf_font_path() -> str:
    """
    返回可用于 PDF 导出的中文字体路径（优先系统字体，其次缓存字体）。
    供 fpdf 等需要直接加载字体文件的库使用。
    """
    # 优先 Windows 系统字体
    if platform.system() == "Windows":
        candidates = [
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
            r"C:\Windows\Fonts\msyh.ttf",
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\msyhbd.ttc",
        ]
        for p in candidates:
            if os.path.exists(p):
                return p

    # 其次项目内置字体
    bundled = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "fonts", FONT_FILENAME,
    )
    if os.path.exists(bundled):
        return bundled

    # 最后使用缓存/下载字体
    return _ensure_cached_font()
