"""
企业政策硬条件匹配引擎
用途：基于企业画像和政策库，输出每条政策的诊断结果
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple


def load_json(file_path: str) -> Dict[str, Any]:
    """加载 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_policies() -> List[Dict[str, Any]]:
    """加载政策库：优先 v2 结构化政策库，缺失时回退 v1"""
    import os
    for path in ("data/policies_v2.json", "data/policies.json"):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    return []


# 企业画像字段 → 中文可读名称
FIELD_LABELS = {
    "name": "企业名称",
    "province": "省份",
    "city": "城市",
    "region": "所在地区",
    "industry": "所属行业",
    "sub_industry": "细分行业",
    "scale": "企业规模",
    "employees": "员工人数",
    "founded_year": "成立年份",
    "years_in_operation": "成立年限",
    "years_in_segment": "细分领域从业年限",
    "revenue": "上年度营收",
    "profit": "上年度利润",
    "revenue_growth_2yr": "近两年营收增长率",
    "total_assets": "资产总额",
    "rd_investment": "研发投入",
    "rd_ratio": "研发投入占比",
    "rd_team_size": "研发人员数量",
    "rd_team_ratio": "研发人员占比",
    "rd_equipment": "研发设备",
    "rd_investment_growth": "研发投入增长率",
    "rd_accounting_system": "研发准备金制度",
    "invention_patents": "发明专利数量",
    "utility_models": "实用新型专利数量",
    "software_copyrights": "软件著作权数量",
    "trademarks": "商标数量",
    "qualifications": "企业资质",
    "is_high_tech_enterprise": "国家高新技术企业",
    "is_high_tech_field": "高新技术领域",
    "high_tech_income_ratio": "高新技术产品收入占比",
    "has_major_accident": "近三年重大事故",
    "market_share_proof": "市场占有率证明",
    "project_completion": "项目完成情况",
    "is_first_application": "首次申报",
    "has_sales_contract": "销售合同",
    "has_test_report": "检测报告",
    "has_mes": "MES系统",
    "has_mes_erp": "MES/ERP系统",
    "equipment_networking_rate": "设备联网率",
    "smart_equipment_investment": "智能化设备投资",
    "self_funding_ratio": "自筹资金比例",
    "team_core_members": "核心团队成员",
    "total_project_investment": "项目总投资",
    "core_product": "核心产品",
}


def label_for(field_name: str) -> str:
    """获取字段的中文名称，没有映射时返回原值"""
    return FIELD_LABELS.get(field_name, field_name)


def humanize_gap_item(item: str) -> str:
    """
    将失败/缺失项中的英文字段名翻译成中文标签。
    用于兼容旧缓存结果（key 为英文）以及显示时的统一美化。
    """
    if not item:
        return item
    # 优先按中文/英文冒号拆分，只处理 key 部分
    for sep in ("：", ":"):
        if sep in item:
            key, rest = item.split(sep, 1)
            return f"{label_for(key.strip())}：{rest.lstrip()}"
    return label_for(item)


def save_json(file_path: str, data: Dict[str, Any]) -> None:
    """保存 JSON 文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# v2 条件项中"取值字段"的兼容别名：不同数据源营收字段名不同
_FIELD_ALIASES = {
    "annual_revenue": ["annual_revenue", "revenue"],
    "revenue": ["revenue", "annual_revenue"],
}


def _field_value(enterprise: Dict[str, Any], field: str) -> Any:
    """取企业字段值，支持别名兼容"""
    for key in _FIELD_ALIASES.get(field, [field]):
        if key in enterprise:
            return enterprise.get(key)
    return enterprise.get(field)


def check_condition_v2(value: Any, item: Dict[str, Any]) -> Tuple[bool, str]:
    """检查 v2 标准条件项（operator/value 规范化）"""
    label = label_for(item.get("field", ""))
    operator = item.get("operator")
    required = item.get("value")

    if value is None and operator != "required":
        return False, f"{label}：数据缺失，需补充"

    if operator == ">=":
        if value < required:
            return False, f"{label}：当前 {value}，要求 ≥ {required}，差 {required - value:.2f}"
    elif operator == "<=":
        if value > required:
            return False, f"{label}：当前 {value}，要求 ≤ {required}，超出 {value - required:.2f}"
    elif operator == "==":
        if bool(value) != bool(required):
            return False, f"{label}：当前为“{'是' if value else '否'}”，政策要求必须为“{'是' if required else '否'}”"
    elif operator == "required":
        if bool(value) != bool(required):
            current = "是" if value else "否"
            expected = "是" if required else "否"
            return False, f"{label}：当前为“{current}”，政策要求必须为“{expected}”"
    elif operator == "contains":
        values = value if isinstance(value, list) else [value]
        missing = [v for v in required if v not in values]
        if missing:
            return False, f"{label}：缺少资质 {missing}"
    elif operator == "in":
        if value not in required:
            return False, f"{label}：当前 {value}，不在允许范围 {required} 内"
    elif operator == "or":
        values = value if isinstance(value, list) else [value]
        if not any(v in required for v in values):
            return False, f"{label}：当前 {value}，需满足其中之一 {required}"

    return True, f"{label}：满足"


def check_tier_condition(enterprise: Dict[str, Any], item: Dict[str, Any],
                         tiers: Dict[str, Any]) -> Tuple[bool, str]:
    """
    检查分档条件（如高企研发费用比例按营收三档）。
    按 basis_field 定位档位后，校验该档要求的字段阈值。
    """
    label = label_for(item.get("field", ""))
    tier_key = item.get("tier_key")
    tier_def = tiers.get(tier_key, {})
    basis_field = tier_def.get("basis_field", "")
    basis = _field_value(enterprise, basis_field)

    if basis is None:
        return False, f"{label}：{label_for(basis_field)}数据缺失，无法确定适用档位"

    band_hit = None
    for band in tier_def.get("bands", []):
        lo = band.get("min", float("-inf"))
        hi = band.get("max", float("inf"))
        in_band = (basis >= lo) if hi == float("inf") else (lo <= basis < hi)
        if in_band:
            band_hit = band
            break

    if band_hit is None:
        return False, f"{label}：未匹配到适用档位，请人工核对"

    require = band_hit.get("require", {})
    target_field = item.get("field")
    if target_field not in require:
        return True, f"{label}：满足（{band_hit.get('desc', '')}）"

    value = _field_value(enterprise, target_field)
    threshold = require[target_field]
    if value is None:
        return False, f"{label}：数据缺失，需补充（适用档位：{band_hit.get('desc', '')}）"
    if value < threshold:
        return False, (f"{label}：当前 {value}，要求 ≥ {threshold}，差 {threshold - value:.2f}"
                       f"（适用档位：{band_hit.get('desc', '')}）")
    return True, f"{label}：满足（{band_hit.get('desc', '')}）"


def check_exclusion(enterprise: Dict[str, Any], item: Dict[str, Any]) -> Tuple[bool, str]:
    """检查一票否决项；返回 (触发否决, 说明)"""
    label = label_for(item.get("field", ""))
    value = _field_value(enterprise, item.get("field", ""))
    if value is None:
        return False, f"{label}：未声明，默认无（建议核实）"
    triggered = bool(value) == bool(item.get("value"))
    if triggered:
        return True, f"{label}：{item.get('desc', '触及否决情形')}（一票否决）"
    return False, f"{label}：无（满足）"


def check_prerequisite(enterprise: Dict[str, Any], prereq_ids: List[str],
                       policy_map: Dict[str, Dict[str, Any]]) -> List[str]:
    """检查政策依赖链前置资质；返回未满足的前置政策名称列表"""
    quals = enterprise.get("qualifications") or []
    missing = []
    for pid in prereq_ids:
        name = (policy_map.get(pid) or {}).get("policy_name", pid)
        if not any(q in name or name in q for q in quals):
            missing.append(name)
    return missing


def check_condition(value: Any, condition: Dict[str, Any], condition_name: str) -> Tuple[bool, str]:
    """检查单个条件是否满足"""
    label = label_for(condition_name)
    if value is None:
        return False, f"{label}：数据缺失，需补充"

    if 'min' in condition:
        if value < condition['min']:
            gap = condition['min'] - value
            return False, f"{label}：当前 {value}，要求 ≥ {condition['min']}，差 {gap:.2f}"

    if 'max' in condition:
        if value > condition['max']:
            gap = value - condition['max']
            return False, f"{label}：当前 {value}，要求 ≤ {condition['max']}，超出 {gap:.2f}"

    if 'required' in condition:
        required = condition['required']
        if bool(value) != required:
            current = "是" if value else "否"
            expected = "是" if required else "否"
            return False, f"{label}：当前为“{current}”，政策要求必须为“{expected}”"

    if 'contains' in condition:
        required_items = condition['contains']
        if not isinstance(value, list):
            value = [value]
        missing = [item for item in required_items if item not in value]
        if missing:
            return False, f"{label}：缺少资质 {missing}"

    if 'in' in condition:
        allowed = condition['in']
        if value not in allowed:
            return False, f"{label}：当前 {value}，不在允许范围 {allowed} 内"

    if 'or' in condition:
        options = condition['or']
        values = value if isinstance(value, list) else [value]
        if not any(v in options for v in values):
            return False, f"{label}：当前 {value}，需满足其中之一 {options}"

    return True, f"{label}：满足"


def match_policy(enterprise: Dict[str, Any], policy: Dict[str, Any],
                 policy_map: Dict[str, Dict[str, Any]] = None) -> Dict[str, Any]:
    """对单条政策进行硬条件匹配（v2 conditions 优先，兼容 v1 hard_conditions）"""
    if "conditions" in policy:
        return match_policy_v2(enterprise, policy, policy_map or {})
    return match_policy_v1(enterprise, policy)


def match_policy_v2(enterprise: Dict[str, Any], policy: Dict[str, Any],
                    policy_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """v2 结构化政策匹配：标准条件项 + 分档条件 + 一票否决 + 政策依赖链"""
    passed, failed, unknown = [], [], []

    # 时效：非"有效"状态的政策不出申报结论
    status = policy.get("status", "有效")
    if status not in ("有效", None):
        return _result(policy, "持续关注", f"政策当前状态为「{status}」，仅作参考",
                       passed, failed + [f"政策状态：{status}"], unknown)

    # 地区匹配（与 v1 同一套逻辑）
    policy_regions = policy.get("region", [])
    enterprise_region = str(enterprise.get('province', '')) + str(enterprise.get('city', ''))
    region_match = any(
        r == '全国' or (r in enterprise_region or enterprise_region in r)
        for r in policy_regions
    )
    if not region_match:
        failed.append(f"{label_for('region')}：当前 {enterprise.get('region')}，政策适用 {policy_regions}")
    else:
        passed.append(f"{label_for('region')}：{enterprise.get('region')} 在政策适用范围内")

    conditions = policy.get("conditions", {})

    # 政策依赖链：前置资质
    prereq_missing = check_prerequisite(
        enterprise, policy.get("policy_chain", {}).get("prerequisite", []), policy_map)
    for name in prereq_missing:
        failed.append(f"前置资质：需先获得《{name}》")

    # 标准条件项（tier_key 项走分档校验）
    tiers = conditions.get("tiers", {})
    for item in conditions.get("hard", []):
        if item.get("tier_key"):
            ok, message = check_tier_condition(enterprise, item, tiers)
        else:
            value = _field_value(enterprise, item.get("field", ""))
            ok, message = check_condition_v2(value, item)
        if ok:
            passed.append(message)
        elif "数据缺失" in message:
            unknown.append(message)
        else:
            failed.append(message)

    # 一票否决项
    veto_triggered = False
    for item in conditions.get("exclusions", []):
        triggered, message = check_exclusion(enterprise, item)
        if triggered:
            veto_triggered = True
            failed.append(message)
        else:
            passed.append(message)

    if veto_triggered:
        diagnosis, reason = "暂不适合", "触及一票否决情形"
    else:
        diagnosis, reason = determine_diagnosis(passed, failed, unknown, policy)

    return _result(policy, diagnosis, reason, passed, failed, unknown)


def match_policy_v1(enterprise: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
    """对单条政策进行硬条件匹配"""
    hard_conditions = policy.get('hard_conditions', {})
    passed = []
    failed = []
    unknown = []

    # 地区匹配
    policy_regions = policy.get('region', [])
    enterprise_region = enterprise.get('province', '') + enterprise.get('city', '')
    region_match = False
    for r in policy_regions:
        if r == '全国':
            region_match = True
            break
        if r in enterprise_region or enterprise_region in r:
            region_match = True
            break
    if not region_match:
        failed.append(f"{label_for('region')}：当前 {enterprise.get('region')}，政策适用 {policy_regions}")
    else:
        passed.append(f"{label_for('region')}：{enterprise.get('region')} 在政策适用范围内")

    # 逐项检查硬条件
    for condition_name, condition in hard_conditions.items():
        value = enterprise.get(condition_name)
        is_passed, message = check_condition(value, condition, condition_name)

        if is_passed:
            passed.append(message)
        elif "数据缺失" in message:
            unknown.append(message)
        else:
            failed.append(message)

    diagnosis, reason = determine_diagnosis(passed, failed, unknown, policy)

    return _result(policy, diagnosis, reason, passed, failed, unknown)


def _result(policy: Dict[str, Any], diagnosis: str, reason: str,
            passed: List[str], failed: List[str], unknown: List[str]) -> Dict[str, Any]:
    """统一匹配结果结构（v1/v2 共用）"""
    benefit = policy.get('benefit', '')
    if isinstance(benefit, dict):
        benefit = benefit.get('summary', '')
    return {
        "policy_id": policy['policy_id'],
        "policy_name": policy['policy_name'],
        "level": policy['level'],
        "category": policy['category'],
        "deadline": policy.get('deadline') or policy.get('application_deadline', ''),
        "diagnosis": diagnosis,
        "reason": reason,
        "passed_count": len(passed),
        "failed_count": len(failed),
        "unknown_count": len(unknown),
        "passed": passed,
        "failed": failed,
        "unknown": unknown,
        "benefit": benefit,
        "priority": policy.get('priority', '中')
    }


def determine_diagnosis(passed: List[str], failed: List[str], unknown: List[str], policy: Dict[str, Any]) -> Tuple[str, str]:
    """根据条件检查结果判断诊断结果"""
    deadline_str = policy.get('deadline') or policy.get('application_deadline', '')

    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            if deadline < datetime.now():
                return "持续关注", "政策已过期"
            days_left = (deadline - datetime.now()).days
            if days_left < 7:
                return "立即申报", f"即将截止（剩 {days_left} 天），如条件满足请立即申报"
        except ValueError:
            pass

    total_conditions = len(passed) + len(failed) + len(unknown)
    if total_conditions > 0 and len(unknown) / total_conditions > 0.5:
        return "持续关注", "关键数据缺失，补充后可重新诊断"

    if len(failed) == 0 and len(unknown) == 0:
        return "立即申报", "所有硬条件均满足"

    if len(failed) > 0:
        if len(failed) <= 2:
            return "培育申报", f"存在 {len(failed)} 项可补齐差距，建议 1-2 年内培育"
        else:
            return "暂不适合", f"存在 {len(failed)} 项差距，短期内难以补齐"

    return "持续关注", "部分条件数据缺失，补充后进一步判断"


def calculate_match_score(result: Dict[str, Any]) -> int:
    """计算匹配度分数"""
    total = result['passed_count'] + result['failed_count'] + result['unknown_count']
    if total == 0:
        return 0
    score = (result['passed_count'] + result['unknown_count'] * 0.3) / total * 100
    return min(int(score), 100)


def run_diagnosis(enterprise: Dict[str, Any], policies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """运行完整诊断"""
    policy_map = {p['policy_id']: p for p in policies}
    results = []
    for policy in policies:
        result = match_policy(enterprise, policy, policy_map)
        result['match_score'] = calculate_match_score(result)
        results.append(result)

    # 按诊断优先级排序
    diagnosis_order = {"立即申报": 0, "培育申报": 1, "持续关注": 2, "暂不适合": 3}
    results.sort(key=lambda x: (diagnosis_order.get(x['diagnosis'], 99), -x['match_score']))

    diagnosis_count = {}
    for r in results:
        diagnosis_count[r['diagnosis']] = diagnosis_count.get(r['diagnosis'], 0) + 1

    return {
        "enterprise_name": enterprise.get('name', ''),
        "diagnosis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "summary": diagnosis_count,
        "results": results
    }
