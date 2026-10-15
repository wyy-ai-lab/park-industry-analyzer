"""
政策库 v1 → v2 迁移脚本
========================
将 data/policies.json（v1 平铺 hard_conditions）迁移为 v2 结构化政策库
data/policies_v2.json（见 政策条件库设计.md）。

迁移内容：
- hard_conditions 平铺项 → conditions.hard 标准条件项（operator/value 规范化）
- has_major_accident(required=false) → conditions.exclusions（一票否决）
- HF-001 高企研发费用比例 → conditions.tiers 营收分档（修复 v1 把三档规则
  硬编码为"5000万-2亿档 4%"导致 2 亿以上企业被误判不达标的 bug）
- 前置资质依赖 → policy_chain.prerequisite（HF-003/018/024）
- 补充 status / review / application 等治理字段

运行：python scripts/migrate_policies_v1_to_v2.py
"""

import json

SRC = "data/policies.json"
DST = "data/policies_v2.json"

# 前置政策依赖链：policy_id -> 前置 policy_id 列表
POLICY_CHAIN = {
    "HF-003": ["HF-002"],   # 小巨人 ← 省专精特新
    "HF-018": ["HF-006"],   # 国家级企业技术中心 ← 省级
    "HF-024": ["HF-003"],   # 重点小巨人 ← 国家级小巨人
}

# 高企研发费用比例三档规则（国科发火〔2016〕32号）
HF001_RD_TIERS = {
    "revenue_band": {
        "basis_field": "annual_revenue",
        "basis_desc": "最近一年销售收入（万元）",
        "bands": [
            {"max": 5000, "require": {"rd_ratio": 0.05},
             "desc": "最近一年销售收入 ≤ 5,000 万元，研发费用占比 ≥ 5%"},
            {"min": 5000, "max": 20000, "require": {"rd_ratio": 0.04},
             "desc": "最近一年销售收入 5,000 万–2 亿元，研发费用占比 ≥ 4%"},
            {"min": 20000, "require": {"rd_ratio": 0.03},
             "desc": "最近一年销售收入 > 2 亿元，研发费用占比 ≥ 3%"},
        ],
        "source_quote": "最近一年销售收入小于5,000万元（含）的企业，比例不低于5%；"
                        "在5,000万元至2亿元（含）的企业，比例不低于4%；"
                        "在2亿元以上的企业，比例不低于3%。",
    }
}


def convert_condition(field: str, cond: dict) -> dict:
    """v1 平铺条件 → v2 标准条件项"""
    item = {"field": field, "desc": cond.get("desc", "")}
    if "min" in cond:
        item["operator"] = ">="
        item["value"] = cond["min"]
    elif "max" in cond:
        item["operator"] = "<="
        item["value"] = cond["max"]
    elif "required" in cond:
        item["operator"] = "required"
        item["value"] = bool(cond["required"])
    elif "contains" in cond:
        item["operator"] = "contains"
        item["value"] = cond["contains"]
    elif "in" in cond:
        item["operator"] = "in"
        item["value"] = cond["in"]
    elif "or" in cond:
        item["operator"] = "or"
        item["value"] = cond["or"]
    else:
        item["operator"] = "unknown"
        item["value"] = None
    item["source_quote"] = None  # 人工补录原文出处后 confidence 可升 high
    return item


def migrate(policy: dict) -> dict:
    pid = policy["policy_id"]
    hard, exclusions = [], []

    for field, cond in policy.get("hard_conditions", {}).items():
        # 否决项独立成块（近 N 年无重大事故类）
        if field == "has_major_accident" and not cond.get("required", True):
            exclusions.append({
                "field": field,
                "operator": "==",
                "value": True,
                "effect": "一票否决",
                "desc": cond.get("desc", "近三年无重大安全/质量/环保事故"),
                "source_quote": None,
            })
            continue
        hard.append(convert_condition(field, cond))

    conditions = {"hard": hard, "exclusions": exclusions, "soft": []}

    # HF-001：以分档条件替换硬编码的单一研发占比阈值
    if pid == "HF-001":
        hard[:] = [c for c in hard if c["field"] != "rd_ratio"]
        hard.append({
            "field": "rd_ratio",
            "operator": ">=",
            "tier_key": "revenue_band",
            "desc": "研发费用占比达到营收对应档位要求（三档制）",
            "source_quote": HF001_RD_TIERS["revenue_band"]["source_quote"],
        })
        conditions["tiers"] = HF001_RD_TIERS

    return {
        "policy_id": pid,
        "schema_version": "2.0",
        "policy_name": policy["policy_name"],
        "level": policy["level"],
        "region": policy.get("region", []),
        "category": policy.get("category", ""),
        "status": "有效",
        "application_deadline": policy.get("deadline", ""),
        "application": {
            "window": None,
            "channel": None,
            "materials": [],
            "review_cycle_months": None,
        },
        "conditions": conditions,
        "benefit": {"summary": policy.get("benefit", ""), "lump_sum": None, "tax": None},
        "policy_chain": {
            "prerequisite": POLICY_CHAIN.get(pid, []),
            "unlocks": [k for k, v in POLICY_CHAIN.items() if pid in v],
        },
        "priority": policy.get("priority", "中"),
        "review": {
            "structured_by": "v1-migration",
            "reviewed_by": None,
            "reviewed_at": None,
            "confidence": "medium",
        },
        "version": 1,
        "updated_at": "2026-10-15",
    }


def main() -> None:
    with open(SRC, encoding="utf-8") as f:
        v1 = json.load(f)
    v2 = [migrate(p) for p in v1]
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(v2, f, ensure_ascii=False, indent=2)
    print(f"✅ {SRC}（{len(v1)} 条）→ {DST}")
    print("   含分档条件: HF-001 | 依赖链:",
          {k: v for k, v in POLICY_CHAIN.items()})


if __name__ == "__main__":
    main()
