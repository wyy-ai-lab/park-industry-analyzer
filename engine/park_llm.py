"""
园区 LLM 诊断
根据园区指标生成结构化诊断结论与建议。
"""

import json
import os
from typing import Dict, List, Any, Optional


PARK_DIAGNOSIS_PROMPT = """你是一位资深的产业规划与园区经济专家。请根据以下园区产业分析数据，生成一份结构化的诊断结论与发展建议。

【园区名称】
{park_name}

【核心指标】
- 企业总数：{enterprise_count} 家
- 年产值：{total_revenue} 亿元
- 员工总数：{total_employees} 人
- 高新技术企业：{high_tech_count} 家
- 专精特新/小巨人：{little_giant_count} 家
- 产业链完整度评分：{completeness_score} 分
- 本地配套率：{local_support_rate}%

【产业链层级分布】
{chain_distribution}

【产业领域分布】
{sub_industry_distribution}

【强势环节】
{strong_segments}

【薄弱环节】
{weak_segments}

【缺失环节】
{missing_segments}

【风险环节】
{risk_segments}

请输出以下 JSON 格式：
{{
  "overall_assessment": "200字以内的整体判断",
  "core_strengths": ["优势1", "优势2", "优势3"],
  "key_gaps": ["短板1", "短板2", "短板3"],
  "investment_suggestions": ["招商补链建议1", "招商补链建议2", "招商补链建议3"],
  "cultivation_suggestions": ["企业梯度培育建议1", "企业梯度培育建议2", "企业梯度培育建议3"],
  "policy_suggestions": ["政策培育建议1", "政策培育建议2", "政策培育建议3"],
  "risk_warning": "100字以内的风险提醒"
}}

注意：
1. 只输出 JSON，不要输出其他文字
2. 建议要具体、可操作，避免空泛
3. 紧密结合新能源汽车产业链特点
"""


def _call_anthropic(prompt: str, api_key: str) -> Optional[str]:
    """调用 Anthropic Claude API"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Anthropic API 调用失败: {e}")
        return None


def _call_openai(prompt: str, api_key: str) -> Optional[str]:
    """调用 OpenAI API"""
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 调用失败: {e}")
        return None


def _parse_llm_response(response_text: str) -> Dict[str, Any]:
    """解析 LLM 返回的 JSON"""
    if not response_text:
        return {}
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    import re
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return {}


def _format_distribution(dist: Dict[str, int]) -> str:
    return "\n".join([f"- {k}：{v}" for k, v in dist.items()])


def generate_diagnosis(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成园区产业诊断结论。

    如果配置了 ANTHROPIC_API_KEY 或 OPENAI_API_KEY，则调用真实 LLM；
    否则返回基于模板的诊断结论。
    """
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    api_key = None

    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")

    totals = metrics.get("totals", {})
    segment_strength = metrics.get("segment_strength", {})

    prompt = PARK_DIAGNOSIS_PROMPT.format(
        park_name=metrics.get("park_name", "未知园区"),
        enterprise_count=metrics.get("total_enterprises", 0),
        total_revenue=totals.get("total_revenue", 0),
        total_employees=totals.get("total_employees", 0),
        high_tech_count=totals.get("high_tech_count", 0),
        little_giant_count=totals.get("little_giant_count", 0),
        completeness_score=metrics.get("completeness_score", 0),
        local_support_rate=metrics.get("local_support_rate", 0),
        chain_distribution=_format_distribution(metrics.get("chain_distribution", {})),
        sub_industry_distribution=_format_distribution(metrics.get("sub_industry_distribution", {})),
        strong_segments="、".join(segment_strength.get("strong", [])) or "无",
        weak_segments="、".join(segment_strength.get("weak", [])) or "无",
        missing_segments="、".join(segment_strength.get("missing", [])) or "无",
        risk_segments="、".join(segment_strength.get("risk", [])) or "无",
    )

    if api_key:
        if provider == "anthropic":
            response_text = _call_anthropic(prompt, api_key)
        else:
            response_text = _call_openai(prompt, api_key)

        if response_text:
            result = _parse_llm_response(response_text)
            if result:
                result["provider"] = provider
                result["mode"] = "llm"
                _enrich_diagnosis(result, metrics)
                return result

    # 模板模式
    result = _template_diagnosis(metrics)
    _enrich_diagnosis(result, metrics)
    return result


def _build_action_items(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    """基于指标生成结构化行动清单（建议-依据-优先级-时限）"""
    segment_strength = metrics.get("segment_strength", {})
    local_rate = metrics.get("local_support_rate", 0)
    completeness = metrics.get("completeness_score", 0)
    missing = segment_strength.get("missing", [])
    weak = segment_strength.get("weak", [])
    risk = segment_strength.get("risk", [])

    items = []
    if missing:
        items.append({
            "category": "招商补链",
            "action": f"重点招引 {'、'.join(missing[:2])} 等缺失环节龙头企业",
            "basis": f"上述环节园区尚无布局，拉低产业链完整度（当前 {completeness} 分）",
            "priority": "高",
            "timeline": "6–12 个月",
        })
    if risk:
        items.append({
            "category": "招商补链",
            "action": f"布局 {'、'.join(risk[:2])} 等核心器件项目，降低断链风险",
            "basis": "该环节对外依赖度高，属于供应链安全关键节点",
            "priority": "高",
            "timeline": "6–12 个月",
        })
    items.append({
        "category": "企业培育",
        "action": "建立高企、小巨人梯度培育台账，一企一策跟踪辅导",
        "basis": f"园区高企 {metrics.get('totals', {}).get('high_tech_count', 0)} 家、小巨人 {metrics.get('totals', {}).get('little_giant_count', 0)} 家，梯队仍有扩容空间",
        "priority": "中",
        "timeline": "持续推进",
    })
    if weak:
        items.append({
            "category": "企业培育",
            "action": f"支持 {'、'.join(weak[:2])} 环节企业技改扩产",
            "basis": "该环节已有企业布局但规模偏小、技术偏弱，培育见效快于新引进",
            "priority": "中",
            "timeline": "1–2 年",
        })
    items.append({
        "category": "政策支持",
        "action": "出台关键环节专项扶持政策，配套产业引导基金",
        "basis": f"本地配套率 {local_rate}%，上游材料与核心器件环节缺乏本地供给",
        "priority": "中",
        "timeline": "6 个月内出台",
    })
    items.append({
        "category": "政策支持",
        "action": "搭建产学研协同平台，定向输送研发人才",
        "basis": f"园区研发人员合计约 {metrics.get('innovation', {}).get('total_rd_personnel', 0)} 人，关键材料与芯片环节人才密度不足",
        "priority": "低",
        "timeline": "1–2 年",
    })
    return items


def _build_risk_items(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    """生成风险-影响-应对三行式风险清单"""
    segment_strength = metrics.get("segment_strength", {})
    risk_segments = segment_strength.get("risk", [])
    missing = segment_strength.get("missing", [])

    items = []
    for seg in risk_segments[:3]:
        items.append({
            "risk": f"{seg}环节断供风险",
            "impact": "整车与电池企业生产排产受外部供应波动影响，成本不可控",
            "mitigation": "招引替代供应商落地 + 与现有供应商签订长协锁量",
        })
    for seg in missing[:2]:
        items.append({
            "risk": f"{seg}环节缺失，对外依存度高",
            "impact": "关键环节采购依赖外地/进口，议价能力与交付周期受制于人",
            "mitigation": "将该环节列入招商目标清单，给予落地政策包优先支持",
        })
    return items


def _enrich_diagnosis(diagnosis: Dict[str, Any], metrics: Dict[str, Any]) -> None:
    """为诊断结论补充结构化行动清单、风险应对与培育企业点名（就地修改）"""
    diagnosis["action_items"] = _build_action_items(metrics)
    diagnosis["risk_items"] = _build_risk_items(metrics)
    diagnosis["enterprise_callouts"] = metrics.get("cultivation_candidates", [])


def _template_diagnosis(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """基于模板生成诊断结论（演示模式）"""
    park_name = metrics.get("park_name", "该园区")
    completeness = metrics.get("completeness_score", 0)
    local_rate = metrics.get("local_support_rate", 0)
    totals = metrics.get("totals", {})
    segment_strength = metrics.get("segment_strength", {})

    strong = segment_strength.get("strong", [])
    weak = segment_strength.get("weak", [])
    missing = segment_strength.get("missing", [])
    risk = segment_strength.get("risk", [])

    assessment = (
        f"{park_name}已形成以动力电池和整车制造为核心的产业格局，"
        f"中游制造环节优势明显，但上游原材料与核心电子元器件存在短板。"
        f"产业链完整度为 {completeness} 分，本地配套率约 {local_rate}%，"
        f"整体具备较好的产业基础，但需重点补强关键环节以提升产业链韧性。"
    )

    core_strengths = [
        f"动力电池产业链较为完整，强势环节包括：{'、'.join(strong[:3])}",
        f"企业总数 {totals.get('enterprise_count', 0)} 家，年产值约 {totals.get('total_revenue', 0)} 亿元",
        "链主企业与骨干企业带动效应明显，高新技术企业占比高",
    ]

    key_gaps = [
        f"缺失环节：{'、'.join(missing)}，上游原材料对外依赖较大",
        f"薄弱环节：{'、'.join(weak)}，核心技术与产能不足",
        f"风险环节：{'、'.join(risk)}，存在断链风险",
    ]

    investment_suggestions = [
        f"重点招引 {'、'.join(missing[:2])} 等上游核心材料企业，补齐上游短板",
        "引进车规级芯片、高精度传感器等核心电子元器件项目",
        "围绕链主企业开展精准招商，提升本地配套率",
    ]

    cultivation_suggestions = [
        "推动骨干企业向系统集成方向延伸，提升价值链位置",
        "支持科技型中小企业成长为高新技术企业，壮大创新梯队",
        "培育电机电控、智能网联企业向专精特新方向发展",
    ]

    policy_suggestions = [
        "出台专项政策支持动力电池材料、车规芯片等关键环节研发",
        "设立产业引导基金，支持本地企业技术改造与产能扩张",
        "搭建产学研合作平台，强化与中国科学技术大学、合肥工业大学联动",
    ]

    risk_warning = (
        "上游锂盐/锂矿、隔膜等原材料缺失，叠加车规芯片、激光雷达等核心器件薄弱，"
        "可能导致供应链受外部波动影响，建议尽快布局补链。"
    )

    return {
        "overall_assessment": assessment,
        "core_strengths": core_strengths,
        "key_gaps": key_gaps,
        "investment_suggestions": investment_suggestions,
        "cultivation_suggestions": cultivation_suggestions,
        "policy_suggestions": policy_suggestions,
        "risk_warning": risk_warning,
        "provider": "demo",
        "mode": "template",
    }
