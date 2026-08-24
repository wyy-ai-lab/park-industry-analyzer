"""
诊断结果看板辅助模块
用途：计算行动看板指标、截止日状态、结果排序
"""

from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

from .matcher import label_for, humanize_gap_item


# 诊断类型优先级（数字越小越优先）
DIAGNOSIS_PRIORITY = {
    "立即申报": 0,
    "培育申报": 1,
    "持续关注": 2,
    "暂不适合": 3,
}

# 政策自身优先级映射
POLICY_PRIORITY = {
    "高": 0,
    "中": 1,
    "低": 2,
}


def get_deadline_status(deadline_str: str, reference_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    解析政策截止日状态

    返回：
        {
            "days_left": int,      # 剩余天数，已过期为负数
            "is_expired": bool,
            "is_urgent": bool,     # 30 天内截止视为紧急
            "status_text": str     # 用于展示的中文状态
        }
    """
    if reference_date is None:
        reference_date = datetime.now()

    if not deadline_str:
        return {
            "days_left": None,
            "is_expired": False,
            "is_urgent": False,
            "status_text": "未设截止日"
        }

    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
        days_left = (deadline - reference_date).days
        is_expired = days_left < 0
        is_urgent = 0 <= days_left <= 30

        if is_expired:
            status_text = f"已过期 {abs(days_left)} 天"
        elif is_urgent:
            status_text = f"剩 {days_left} 天"
        else:
            status_text = f"剩 {days_left} 天"

        return {
            "days_left": days_left,
            "is_expired": is_expired,
            "is_urgent": is_urgent,
            "status_text": status_text
        }
    except ValueError:
        return {
            "days_left": None,
            "is_expired": False,
            "is_urgent": False,
            "status_text": "截止日格式异常"
        }


def compute_dashboard_metrics(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据诊断结果计算行动看板指标
    """
    results = result.get('results', [])
    summary = result.get('summary', {})

    total = len(results)

    # 计算平均综合匹配度
    scores = [r.get('combined_score', r.get('match_score', 0)) for r in results]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    # 截止日统计
    urgent_count = 0
    expired_count = 0
    nearest_deadline = None
    nearest_days = None

    for r in results:
        status = get_deadline_status(r.get('deadline', ''))
        if status['is_urgent']:
            urgent_count += 1
        if status['is_expired']:
            expired_count += 1
        if status['days_left'] is not None and status['days_left'] >= 0:
            if nearest_days is None or status['days_left'] < nearest_days:
                nearest_days = status['days_left']
                nearest_deadline = r.get('deadline')

    return {
        "total": total,
        "immediate": summary.get('立即申报', 0),
        "cultivate": summary.get('培育申报', 0),
        "watch": summary.get('持续关注', 0),
        "unsuitable": summary.get('暂不适合', 0),
        "avg_score": avg_score,
        "urgent_count": urgent_count,
        "expired_count": expired_count,
        "nearest_deadline": nearest_deadline,
        "nearest_days": nearest_days,
    }


def sort_results_for_display(results: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    """
    按指定方式排序诊断结果

    sort_by 可选：
        - "行动优先级"：按诊断类型优先级 → 综合分数降序 → 截止日由近到远
        - "综合分数降序"：按 combined_score 降序
        - "截止日由近到远"：按截止日升序，无截止日放最后
        - "政策优先级"：按政策自身 priority 升序
    """
    def _action_priority_key(r):
        diag_priority = DIAGNOSIS_PRIORITY.get(r.get('diagnosis', ''), 99)
        score = -(r.get('combined_score', r.get('match_score', 0)))
        deadline_status = get_deadline_status(r.get('deadline', ''))
        days = deadline_status['days_left'] if deadline_status['days_left'] is not None and deadline_status['days_left'] >= 0 else 9999
        policy_priority = POLICY_PRIORITY.get(r.get('priority', '中'), 1)
        return (diag_priority, score, policy_priority, days)

    def _score_key(r):
        return -(r.get('combined_score', r.get('match_score', 0)))

    def _deadline_key(r):
        status = get_deadline_status(r.get('deadline', ''))
        if status['days_left'] is None:
            return 99999
        if status['days_left'] < 0:
            return 99998
        return status['days_left']

    def _policy_priority_key(r):
        return POLICY_PRIORITY.get(r.get('priority', '中'), 1)

    sort_keys = {
        "行动优先级": _action_priority_key,
        "综合分数降序": _score_key,
        "截止日由近到远": _deadline_key,
        "政策优先级": _policy_priority_key,
    }

    key_func = sort_keys.get(sort_by, _action_priority_key)
    return sorted(results, key=key_func)


def get_top_gaps(results: List[Dict[str, Any]], top_n: int = 5) -> List[Tuple[str, int]]:
    """
    统计出现频次最高的不满足条件或缺失数据项

    返回：[(字段/描述, 出现次数), ...]
    """
    gap_counter = {}
    for r in results:
        for item in r.get('failed', []):
            key = humanize_gap_item(item).split('：')[0] if '：' in humanize_gap_item(item) else humanize_gap_item(item).split(':')[0]
            gap_counter[key] = gap_counter.get(key, 0) + 1
        for item in r.get('unknown', []):
            key = humanize_gap_item(item).split('：')[0] if '：' in humanize_gap_item(item) else humanize_gap_item(item).split(':')[0]
            gap_counter[key] = gap_counter.get(key, 0) + 1

    return sorted(gap_counter.items(), key=lambda x: -x[1])[:top_n]
