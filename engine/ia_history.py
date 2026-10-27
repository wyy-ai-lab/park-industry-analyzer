"""
梳理历史记录
============
产业梳理结果落盘保存（data/history/*.json），供内部试用：
- 运行梳理后自动保存，刷新页面/重启应用可恢复最近记录
- 支持多园区多份记录：载入 / 删除
- 同名记录（如同一园区再次梳理）覆盖更新
"""

import json
import re
from datetime import datetime
from pathlib import Path

HISTORY_DIR = Path(__file__).resolve().parent.parent / "data" / "history"


def _slug(name: str) -> str:
    """记录名 → 文件名（保留中文，其余转下划线）"""
    s = re.sub(r'[\\/:*?"<>|\s]+', "_", str(name)).strip("_")
    return (s or "record")[:60]


def _path(name: str) -> Path:
    return HISTORY_DIR / f"{_slug(name)}.json"


def save_record(name: str, result: dict, material: str = "") -> str:
    """保存梳理记录，返回记录名。同名覆盖。"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": name,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "material": material,
        "result": result,
    }
    _path(name).write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    return name


def list_records() -> list:
    """全部记录（新→旧），元素：{name, saved_at}"""
    if not HISTORY_DIR.exists():
        return []
    out = []
    for f in sorted(HISTORY_DIR.glob("*.json"),
                    key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            out.append({"name": data.get("name", f.stem),
                        "saved_at": data.get("saved_at", "")})
        except Exception:  # noqa: BLE001
            continue
    return out


def load_record(name: str) -> dict | None:
    """载入完整记录 {name, saved_at, material, result}；不存在返回 None"""
    p = _path(name)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def delete_record(name: str) -> bool:
    p = _path(name)
    if p.exists():
        p.unlink()
        return True
    return False


def latest_record() -> dict | None:
    """最近一份记录（用于启动时自动恢复）"""
    recs = list_records()
    return load_record(recs[0]["name"]) if recs else None
