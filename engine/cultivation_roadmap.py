"""
个性化培育路线图生成模块

根据政策诊断结果中的 failed/unknown 差距项，为企业生成可执行、分阶段、
带责任人和预估工时的培育路线图。支持规则生成 + LLM 增强两种模式。
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from .matcher import label_for, humanize_gap_item


# ---------------------------------------------------------------------------
# 差距字段 → 培育动作模板映射
# ---------------------------------------------------------------------------

class ActionTemplate:
    """单个培育动作模板"""
    def __init__(
        self,
        field_keys: List[str],
        phase: str,
        title: str,
        description: str,
        owner: str,
        difficulty: str,
        estimated_time: str,
        estimated_cost: str,
        priority: int = 1,
    ):
        self.field_keys = field_keys
        self.phase = phase
        self.title = title
        self.description = description
        self.owner = owner
        self.difficulty = difficulty
        self.estimated_time = estimated_time
        self.estimated_cost = estimated_cost
        self.priority = priority


# phase 取值：immediate(0-30天), short(1-3个月), medium(3-12个月), long(1-2年)
ACTION_TEMPLATES: List[ActionTemplate] = [
    # ----- 立即行动（0-30天）-----
    ActionTemplate(
        field_keys=["has_major_accident"],
        phase="immediate",
        title="排查近三年安全/质量/环保事故",
        description="出具无重大事故说明或整改证明，确保满足政策合规要求。",
        owner="行政人事部/法务",
        difficulty="低",
        estimated_time="1-2周",
        estimated_cost="0-0.5万",
        priority=0,
    ),
    ActionTemplate(
        field_keys=["name", "province", "city", "region"],
        phase="immediate",
        title="确认企业注册地与政策适用区域",
        description="核对营业执照注册地址与政策申报指南中的区域限制，必要时咨询主管部门。",
        owner="行政部",
        difficulty="低",
        estimated_time="1周内",
        estimated_cost="0",
        priority=0,
    ),

    # ----- 短期（1-3个月）-----
    ActionTemplate(
        field_keys=["rd_accounting_system"],
        phase="short",
        title="建立研发费用辅助账/研发准备金制度",
        description="按政策要求建立研发费用归集科目，确保研发费单独核算、凭证完整。",
        owner="财务部",
        difficulty="中",
        estimated_time="1-2个月",
        estimated_cost="0.5-2万",
        priority=1,
    ),
    ActionTemplate(
        field_keys=["rd_investment", "rd_ratio"],
        phase="short",
        title="提升研发投入占比",
        description="梳理当年研发项目，合理归集人员、材料、折旧等费用，确保研发投入满足政策门槛。",
        owner="财务部/研发部",
        difficulty="中",
        estimated_time="1-3个月",
        estimated_cost="视项目而定",
        priority=1,
    ),
    ActionTemplate(
        field_keys=["rd_team_size", "rd_team_ratio"],
        phase="short",
        title="统计并优化研发人员结构",
        description="建立研发人员名册，归集学历、社保、工时证明，确保研发人员占比达标。",
        owner="人力资源部/研发部",
        difficulty="中",
        estimated_time="1-2个月",
        estimated_cost="0-1万",
        priority=1,
    ),
    ActionTemplate(
        field_keys=["high_tech_income_ratio", "is_high_tech_field"],
        phase="short",
        title="高新技术产品收入归集与证明",
        description="梳理高新技术产品清单及对应收入，准备销售合同、发票等收入证明。",
        owner="财务部/市场部",
        difficulty="中",
        estimated_time="1-3个月",
        estimated_cost="0-1万",
        priority=2,
    ),
    ActionTemplate(
        field_keys=["market_share_proof"],
        phase="short",
        title="准备细分市场占有率证明",
        description="委托第三方机构或行业协会出具市场占有率证明，或准备客户证明、销售数据。",
        owner="市场部/第三方机构",
        difficulty="中",
        estimated_time="1-3个月",
        estimated_cost="1-5万",
        priority=2,
    ),
    ActionTemplate(
        field_keys=["has_test_report"],
        phase="short",
        title="补充产品检测报告",
        description="联系具备资质的检测机构，完成核心产品的性能/质量/安全检测。",
        owner="质量部/研发部",
        difficulty="中",
        estimated_time="1-3个月",
        estimated_cost="0.5-3万",
        priority=2,
    ),
    ActionTemplate(
        field_keys=["has_sales_contract"],
        phase="short",
        title="整理销售/用户合同证明",
        description="收集核心产品的销售合同、用户证明、应用案例，作为市场认可度佐证。",
        owner="市场部/销售部",
        difficulty="低",
        estimated_time="2-4周",
        estimated_cost="0",
        priority=2,
    ),

    # ----- 中期（3-12个月）-----
    ActionTemplate(
        field_keys=["invention_patents"],
        phase="medium",
        title="发明专利布局",
        description="围绕核心技术申请发明专利，优先考虑快速预审或优先审查通道。",
        owner="研发部/知识产权代理机构",
        difficulty="高",
        estimated_time="6-18个月",
        estimated_cost="2-10万",
        priority=1,
    ),
    ActionTemplate(
        field_keys=["utility_models"],
        phase="medium",
        title="实用新型专利补充",
        description="针对产品结构、工艺改进申请实用新型专利，作为短期知识产权补充。",
        owner="研发部/知识产权代理机构",
        difficulty="中",
        estimated_time="6-10个月",
        estimated_cost="1-3万",
        priority=2,
    ),
    ActionTemplate(
        field_keys=["software_copyrights"],
        phase="medium",
        title="软件著作权登记",
        description="对软件产品、算法、控制系统进行软著登记，完善知识产权矩阵。",
        owner="研发部/知识产权代理机构",
        difficulty="低",
        estimated_time="1-3个月",
        estimated_cost="0.3-1万",
        priority=2,
    ),
    ActionTemplate(
        field_keys=["trademarks"],
        phase="medium",
        title="商标与品牌保护",
        description="补充核心产品商标注册，完善企业知识产权与品牌形象。",
        owner="市场部/知识产权代理机构",
        difficulty="低",
        estimated_time="6-12个月",
        estimated_cost="0.3-1万",
        priority=3,
    ),
    ActionTemplate(
        field_keys=["qualifications"],
        phase="medium",
        title="前置资质申报",
        description="根据政策要求，先申报高新技术企业、科技型中小企业、专精特新等前置资质。",
        owner="项目申报专员/高管",
        difficulty="高",
        estimated_time="6-18个月",
        estimated_cost="2-10万",
        priority=0,
    ),
    ActionTemplate(
        field_keys=["is_high_tech_enterprise"],
        phase="medium",
        title="国家高新技术企业认定",
        description="按高企认定条件系统准备知识产权、研发费用、高新收入等材料。",
        owner="项目申报专员/研发部/财务部",
        difficulty="高",
        estimated_time="8-12个月",
        estimated_cost="3-8万",
        priority=0,
    ),
    ActionTemplate(
        field_keys=["total_project_investment", "self_funding_ratio"],
        phase="medium",
        title="项目投资与资金筹备",
        description="编制项目投资预算，落实自筹资金来源，准备银行流水、出资证明。",
        owner="财务部/高管",
        difficulty="高",
        estimated_time="3-6个月",
        estimated_cost="视项目规模",
        priority=1,
    ),
    ActionTemplate(
        field_keys=["smart_equipment_investment", "equipment_networking_rate", "has_mes_erp", "has_mes"],
        phase="medium",
        title="智能化/数字化改造规划",
        description="制定设备联网、MES/ERP 部署方案，完成智能化设备投资与数据采集。",
        owner="生产部/IT部",
        difficulty="高",
        estimated_time="6-12个月",
        estimated_cost="50-500万",
        priority=2,
    ),

    # ----- 长期（1-2年）-----
    ActionTemplate(
        field_keys=["revenue", "revenue_growth_2yr"],
        phase="long",
        title="经营规模与成长性提升",
        description="通过市场拓展、产品升级提升营收，保持近两年营收或利润稳定增长。",
        owner="总经理/销售部",
        difficulty="高",
        estimated_time="1-2年",
        estimated_cost="视战略投入",
        priority=2,
    ),
    ActionTemplate(
        field_keys=["employees", "scale"],
        phase="long",
        title="人员规模与企业规模优化",
        description="根据政策对企业规模的要求，合理规划人员招聘与企业规模提升。",
        owner="人力资源部/高管",
        difficulty="中",
        estimated_time="6-12个月",
        estimated_cost="视招聘规模",
        priority=3,
    ),
    ActionTemplate(
        field_keys=["years_in_operation", "years_in_segment"],
        phase="long",
        title="经营年限积累",
        description="持续经营并积累行业经验，满足政策对成立年限或细分市场年限的要求。",
        owner="高管",
        difficulty="低",
        estimated_time="按差距年限",
        estimated_cost="0",
        priority=3,
    ),
    ActionTemplate(
        field_keys=["rd_equipment"],
        phase="long",
        title="研发设备投入",
        description="购置研发用仪器设备，建立研发实验室，确保研发设备原值达标。",
        owner="研发部/采购部",
        difficulty="高",
        estimated_time="6-18个月",
        estimated_cost="20-200万",
        priority=2,
    ),
]


# 阶段展示名称
PHASE_LABELS = {
    "immediate": "立即行动（0-30天）",
    "short": "短期补齐（1-3个月）",
    "medium": "中期培育（3-12个月）",
    "long": "长期建设（1-2年）",
}

PHASE_ORDER = ["immediate", "short", "medium", "long"]


# ---------------------------------------------------------------------------
# 规则生成
# ---------------------------------------------------------------------------

def _extract_field_key(gap_item: str) -> str:
    """从差距描述中提取字段 key"""
    if not gap_item:
        return ""
    for sep in ("：", ":"):
        if sep in gap_item:
            return gap_item.split(sep, 1)[0].strip()
    return gap_item.strip()


def _match_templates_for_gap(gap_item: str) -> List[ActionTemplate]:
    """根据单个差距项匹配适用的动作模板"""
    key = _extract_field_key(gap_item)
    # 先精确匹配 label 对应的原始字段名
    matched = []
    for template in ACTION_TEMPLATES:
        if any(label_for(k) == key or k == key for k in template.field_keys):
            matched.append(template)
    return matched


def _make_action_from_template(
    template: ActionTemplate,
    gap_item: str,
    policy_name: str,
    policy_id: str
) -> Dict[str, Any]:
    """由模板生成具体动作项"""
    return {
        "policy_id": policy_id,
        "policy_name": policy_name,
        "phase": template.phase,
        "phase_label": PHASE_LABELS[template.phase],
        "title": template.title,
        "description": template.description,
        "trigger_gap": humanize_gap_item(gap_item),
        "owner": template.owner,
        "difficulty": template.difficulty,
        "estimated_time": template.estimated_time,
        "estimated_cost": template.estimated_cost,
        "priority": template.priority,
        "status": "待启动",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    }


def generate_policy_roadmap(
    policy_result: Dict[str, Any],
    include_unknown: bool = True,
) -> List[Dict[str, Any]]:
    """
    为单条政策生成培育路线图动作列表。

    参数：
        policy_result: 单条诊断结果
        include_unknown: 是否将缺失数据也纳入路线图

    返回：
        动作列表
    """
    actions = []
    policy_name = policy_result.get("policy_name", "未知政策")
    policy_id = policy_result.get("policy_id", "")

    gap_items = list(policy_result.get("failed", []))
    if include_unknown:
        gap_items.extend(policy_result.get("unknown", []))

    seen_titles: set = set()
    for gap_item in gap_items:
        templates = _match_templates_for_gap(gap_item)
        if not templates:
            # 未匹配到模板的差距，生成通用数据补充动作
            action = {
                "policy_id": policy_id,
                "policy_name": policy_name,
                "phase": "immediate",
                "phase_label": PHASE_LABELS["immediate"],
                "title": f"补充：{humanize_gap_item(gap_item).split('：')[0]}",
                "description": f"针对差距项「{humanize_gap_item(gap_item)}」补充数据或证明材料。",
                "trigger_gap": humanize_gap_item(gap_item),
                "owner": "项目申报专员",
                "difficulty": "低",
                "estimated_time": "1-4周",
                "estimated_cost": "0-0.5万",
                "priority": 2,
                "status": "待启动",
                "created_at": datetime.now().strftime("%Y-%m-%d"),
            }
            if action["title"] not in seen_titles:
                actions.append(action)
                seen_titles.add(action["title"])
            continue

        for template in templates:
            action = _make_action_from_template(template, gap_item, policy_name, policy_id)
            if action["title"] not in seen_titles:
                actions.append(action)
                seen_titles.add(action["title"])

    # 按阶段、优先级排序
    actions.sort(key=lambda x: (PHASE_ORDER.index(x["phase"]), x["priority"]))
    return actions


def generate_enterprise_roadmap(
    diagnosis_result: Dict[str, Any],
    focus_diagnoses: Optional[List[str]] = None,
    top_n: int = 5,
) -> Dict[str, Any]:
    """
    生成企业级培育路线图。

    参数：
        diagnosis_result: 完整诊断结果
        focus_diagnoses: 关注哪些诊断类型（默认：培育申报 + 暂不适合）
        top_n: 最多为前 N 条政策生成详细路线图

    返回：
        {
            "enterprise_name": ...,
            "generated_at": ...,
            "summary": {...},
            "phased_actions": {phase: [actions]},
            "policy_roadmaps": [{policy_id, policy_name, diagnosis, actions}],
        }
    """
    if focus_diagnoses is None:
        focus_diagnoses = ["培育申报", "暂不适合"]

    enterprise_name = diagnosis_result.get("enterprise_name", "未命名企业")
    results = diagnosis_result.get("results", [])

    # 选择需要培育的政策，优先培育申报
    target_results = [
        r for r in results
        if r.get("diagnosis") in focus_diagnoses
    ]
    priority_order = {"培育申报": 0, "暂不适合": 1, "持续关注": 2, "立即申报": 3}
    target_results.sort(
        key=lambda x: (
            priority_order.get(x.get("diagnosis"), 99),
            -(x.get("combined_score", x.get("match_score", 0))),
        )
    )
    target_results = target_results[:top_n]

    policy_roadmaps = []
    all_actions = []

    for r in target_results:
        actions = generate_policy_roadmap(r)
        policy_roadmaps.append({
            "policy_id": r.get("policy_id", ""),
            "policy_name": r.get("policy_name", ""),
            "diagnosis": r.get("diagnosis", ""),
            "combined_score": r.get("combined_score", r.get("match_score", 0)),
            "actions": actions,
        })
        all_actions.extend(actions)

    # 按阶段聚合，同一动作跨政策时合并
    phased_actions: Dict[str, List[Dict[str, Any]]] = {phase: [] for phase in PHASE_ORDER}
    seen_titles: set = set()

    # 先按阶段、优先级排序
    all_actions.sort(key=lambda x: (PHASE_ORDER.index(x["phase"]), x["priority"]))

    for action in all_actions:
        title = action["title"]
        if title in seen_titles:
            # 合并相关政策
            existing = next(a for a in phased_actions[action["phase"]] if a["title"] == title)
            pn = action["policy_name"]
            if pn not in existing.get("related_policies", []):
                existing.setdefault("related_policies", [existing.get("policy_name", "")]).append(pn)
            continue

        seen_titles.add(title)
        action.setdefault("related_policies", [action["policy_name"]])
        phased_actions[action["phase"]].append(action)

    # 统计
    summary = {
        "target_policies": len(target_results),
        "total_actions": len(seen_titles),
        "phase_counts": {phase: len(items) for phase, items in phased_actions.items()},
    }

    return {
        "enterprise_name": enterprise_name,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "focus_diagnoses": focus_diagnoses,
        "summary": summary,
        "phased_actions": phased_actions,
        "policy_roadmaps": policy_roadmaps,
    }


# ---------------------------------------------------------------------------
# LLM 增强
# ---------------------------------------------------------------------------

ROADMAP_LLM_PROMPT = """你是一位资深的企业政策申报辅导专家。请根据以下企业信息和政策诊断结果，生成一份个性化培育路线图。

【企业信息】
{enterprise_info}

【目标政策】
{policy_info}

【差距分析】
{gap_analysis}

请输出以下 JSON 格式：
{{
  "assessment": "对该企业培育该政策的整体判断，200字以内",
  "actions": [
    {{
      "phase": "immediate/short/medium/long",
      "title": "动作标题",
      "description": "具体要做什么，100字以内",
      "owner": "负责部门或角色",
      "difficulty": "低/中/高",
      "estimated_time": "预计耗时",
      "estimated_cost": "预计费用区间",
      "priority": 0-3 数字越小越优先
    }}
  ]
}}

要求：
1. 只输出 JSON，不要其他文字
2. phase 含义：immediate=0-30天，short=1-3个月，medium=3-12个月，long=1-2年
3. actions 数量 4-10 条，覆盖所有关键差距
4. 动作要具体、可执行，避免空泛建议
"""


def _build_enterprise_info(enterprise: Dict[str, Any]) -> str:
    """构建企业信息文本"""
    lines = [
        f"企业名称：{enterprise.get('name', '未知')}",
        f"所属行业：{enterprise.get('industry', '')} - {enterprise.get('sub_industry', '')}",
        f"注册地区：{enterprise.get('region', '')}",
        f"成立年限：{enterprise.get('years_in_operation', '未知')} 年",
        f"企业规模：{enterprise.get('scale', '未知')}，员工 {enterprise.get('employees', '未知')} 人",
        f"上年度营收：{enterprise.get('revenue', '未知')} 万元",
        f"研发投入占比：{enterprise.get('rd_ratio', '未知')}",
        f"研发人员占比：{enterprise.get('rd_team_ratio', '未知')}",
        f"高新技术产品收入占比：{enterprise.get('high_tech_income_ratio', '未知')}",
        f"发明专利：{enterprise.get('invention_patents', 0)} 项",
        f"实用新型：{enterprise.get('utility_models', 0)} 项",
        f"软件著作权：{enterprise.get('software_copyrights', 0)} 项",
        f"已获资质：{'、'.join(enterprise.get('qualifications', []))}",
    ]
    return "\n".join(lines)


def _build_policy_info(policy_result: Dict[str, Any]) -> str:
    """构建政策信息文本"""
    return f"""政策名称：{policy_result.get('policy_name', '')}
政策层级：{policy_result.get('level', '')}
诊断结果：{policy_result.get('diagnosis', '')}
综合分数：{policy_result.get('combined_score', policy_result.get('match_score', 0))} 分
扶持内容：{policy_result.get('benefit', '')}
"""


def _build_gap_analysis(policy_result: Dict[str, Any]) -> str:
    """构建差距分析文本"""
    lines = []
    if policy_result.get("failed"):
        lines.append("不满足条件：")
        for item in policy_result["failed"]:
            lines.append(f"- {humanize_gap_item(item)}")
    if policy_result.get("unknown"):
        lines.append("缺失数据：")
        for item in policy_result["unknown"]:
            lines.append(f"- {humanize_gap_item(item)}")
    return "\n".join(lines) if lines else "无明显差距"


def enhance_roadmap_with_llm(
    enterprise: Dict[str, Any],
    policy_result: Dict[str, Any],
    base_actions: List[Dict[str, Any]],
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    use_demo: bool = False,
) -> List[Dict[str, Any]]:
    """
    使用 LLM 增强培育路线图。

    参数：
        enterprise: 企业画像
        policy_result: 单条政策诊断结果
        base_actions: 规则生成的动作列表（作为 fallback）
        provider: LLM 提供商
        api_key: API 密钥
        use_demo: 是否演示模式

    返回：
        增强后的动作列表
    """
    if use_demo or not api_key:
        return base_actions

    prompt = ROADMAP_LLM_PROMPT.format(
        enterprise_info=_build_enterprise_info(enterprise),
        policy_info=_build_policy_info(policy_result),
        gap_analysis=_build_gap_analysis(policy_result),
    )

    response_text = None
    try:
        if provider == "anthropic":
            from .llm_scorer import call_anthropic
            response_text = call_anthropic(prompt, api_key)
        elif provider == "openai":
            from .llm_scorer import call_openai
            response_text = call_openai(prompt, api_key)
    except Exception as e:
        print(f"LLM 培育路线图增强失败: {e}")

    if not response_text:
        return base_actions

    # 解析 JSON
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                return base_actions
        else:
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    return base_actions
            else:
                return base_actions

    actions = data.get("actions", [])
    if not actions:
        return base_actions

    # 补充元信息
    policy_name = policy_result.get("policy_name", "")
    policy_id = policy_result.get("policy_id", "")
    for action in actions:
        action.setdefault("policy_id", policy_id)
        action.setdefault("policy_name", policy_name)
        action.setdefault("phase_label", PHASE_LABELS.get(action.get("phase", "medium"), action.get("phase", "")))
        action.setdefault("trigger_gap", "由 LLM 根据综合差距生成")
        action.setdefault("status", "待启动")
        action.setdefault("created_at", datetime.now().strftime("%Y-%m-%d"))
        action.setdefault("related_policies", [policy_name])

    # 按阶段、优先级排序
    actions.sort(key=lambda x: (PHASE_ORDER.index(x.get("phase", "medium")), x.get("priority", 2)))
    return actions


def generate_enhanced_roadmap(
    enterprise: Dict[str, Any],
    diagnosis_result: Dict[str, Any],
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    use_demo: bool = False,
    focus_diagnoses: Optional[List[str]] = None,
    top_n: int = 3,
) -> Dict[str, Any]:
    """
    生成增强版企业培育路线图（规则 + LLM）。
    """
    # 先用规则生成
    roadmap = generate_enterprise_roadmap(
        diagnosis_result,
        focus_diagnoses=focus_diagnoses,
        top_n=top_n,
    )

    if use_demo or not api_key:
        roadmap["llm_enhanced"] = False
        roadmap["llm_provider"] = "demo"
        return roadmap

    # 对每条目标政策的动作进行 LLM 增强
    for pr in roadmap["policy_roadmaps"]:
        policy_result = next(
            (r for r in diagnosis_result.get("results", []) if r.get("policy_id") == pr["policy_id"]),
            None
        )
        if policy_result:
            pr["actions"] = enhance_roadmap_with_llm(
                enterprise=enterprise,
                policy_result=policy_result,
                base_actions=pr["actions"],
                provider=provider,
                api_key=api_key,
                use_demo=use_demo,
            )

    # 重新聚合阶段动作
    phased_actions: Dict[str, List[Dict[str, Any]]] = {phase: [] for phase in PHASE_ORDER}
    seen_titles: set = set()
    all_actions = []
    for pr in roadmap["policy_roadmaps"]:
        all_actions.extend(pr["actions"])

    all_actions.sort(key=lambda x: (PHASE_ORDER.index(x.get("phase", "medium")), x.get("priority", 2)))
    for action in all_actions:
        title = action["title"]
        if title in seen_titles:
            existing = next(a for a in phased_actions[action["phase"]] if a["title"] == title)
            pn = action.get("policy_name", "")
            if pn and pn not in existing.get("related_policies", []):
                existing.setdefault("related_policies", [existing.get("policy_name", "")]).append(pn)
            continue
        seen_titles.add(title)
        action.setdefault("related_policies", [action.get("policy_name", "")])
        phased_actions[action["phase"]].append(action)

    roadmap["phased_actions"] = phased_actions
    roadmap["summary"]["total_actions"] = len(seen_titles)
    roadmap["summary"]["phase_counts"] = {phase: len(items) for phase, items in phased_actions.items()}
    roadmap["llm_enhanced"] = True
    roadmap["llm_provider"] = provider

    return roadmap


# ---------------------------------------------------------------------------
# 导出辅助
# ---------------------------------------------------------------------------

def build_roadmap_markdown(roadmap: Dict[str, Any]) -> str:
    """生成培育路线图 Markdown"""
    lines = []
    lines.append(f"# {roadmap.get('enterprise_name', '企业')} 政策培育路线图")
    lines.append("")
    lines.append(f"**生成时间**：{roadmap.get('generated_at', '')}")
    lines.append(f"**覆盖政策数**：{roadmap.get('summary', {}).get('target_policies', 0)} 条")
    lines.append(f"**培育动作总数**：{roadmap.get('summary', {}).get('total_actions', 0)} 项")
    lines.append("")

    phased = roadmap.get("phased_actions", {})
    for phase in PHASE_ORDER:
        actions = phased.get(phase, [])
        if not actions:
            continue
        lines.append(f"## {PHASE_LABELS[phase]}（{len(actions)} 项）")
        lines.append("")
        for i, action in enumerate(actions, 1):
            lines.append(f"### {i}. {action.get('title', '')}")
            lines.append(f"- **说明**：{action.get('description', '')}")
            lines.append(f"- **负责方**：{action.get('owner', '')}")
            lines.append(f"- **难度**：{action.get('difficulty', '')}")
            lines.append(f"- **预计耗时**：{action.get('estimated_time', '')}")
            lines.append(f"- **预计费用**：{action.get('estimated_cost', '')}")
            related = action.get("related_policies", [])
            if related:
                lines.append(f"- **关联政策**：{'、'.join(related)}")
            lines.append("")

    lines.append("---")
    lines.append("*本路线图由企业政策诊断辅导智能体自动生成*")
    return "\n".join(lines)


def save_roadmap(roadmap: Dict[str, Any], file_path: str = "output/cultivation_roadmap.json") -> None:
    """保存路线图到 JSON 文件"""
    import os
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(roadmap, f, ensure_ascii=False, indent=2)


def load_roadmap(file_path: str = "output/cultivation_roadmap.json") -> Optional[Dict[str, Any]]:
    """从 JSON 文件加载路线图"""
    import os
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
