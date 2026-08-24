"""
LLM 软条件打分模块
用途：对企业进行政策软条件评估
"""

import json
import os
from typing import Dict, List, Any, Optional


SOFT_CONDITION_PROMPT = """你是一位资深的政策申报评审专家，擅长评估企业与政策的匹配度。

请根据以下【企业信息】和【政策信息】，进行软条件评估。

【企业信息】
企业名称：{name}
所属行业：{industry}
细分领域：{sub_industry}
注册地区：{region}
成立年限：{years_in_operation} 年
企业规模：{scale}
员工人数：{employees} 人
上年度营收：{revenue} 万元
上年度利润：{profit} 万元
已获资质：{qualifications}
发明专利：{invention_patents} 项
实用新型专利：{utility_models} 项
软件著作权：{software_copyrights} 项
研发投入占比：{rd_ratio}
研发人员占比：{rd_team_ratio}
高新技术产品收入占比：{high_tech_income_ratio}
核心产品：{core_product}

【政策信息】
政策名称：{policy_name}
政策层级：{policy_level}
政策类别：{policy_category}
扶持内容：{policy_benefit}
硬条件诊断结果：{hard_diagnosis}
已满足硬条件：{passed_conditions}
不满足硬条件：{failed_conditions}
缺失数据：{unknown_conditions}

请输出以下内容的 JSON 格式：
{{
  "soft_score": 0-100 的整数,
  "assessment": "对该企业与政策软条件匹配度的综合评价，200字以内",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["短板1", "短板2"],
  "cultivation_suggestions": ["建议1", "建议2"],
  "confidence": "高/中/低"
}}

评分标准：
- 90-100：软条件非常优秀，明显符合政策优先支持方向
- 70-89：软条件较好，具备较强竞争力
- 50-69：软条件一般，需要针对性补强
- 30-49：软条件较弱，培育周期较长
- 0-29：软条件明显不匹配

注意：
1. 只输出 JSON，不要输出其他文字
2. 评价要客观、具体，避免空泛
3. 优势、短板、建议各 2-4 条
"""


MATERIAL_OUTLINE_PROMPT = """你是一位资深的政策申报辅导专家，擅长根据企业情况和政策要求生成申报材料大纲。

请根据以下【企业信息】和【政策信息】，为该企业生成《{policy_name}》的申报材料大纲。

【企业信息】
企业名称：{name}
所属行业：{industry}
细分领域：{sub_industry}
注册地区：{region}
成立年限：{years_in_operation} 年
企业规模：{scale}
员工人数：{employees} 人
上年度营收：{revenue} 万元
上年度利润：{profit} 万元
已获资质：{qualifications}
发明专利：{invention_patents} 项
实用新型专利：{utility_models} 项
软件著作权：{software_copyrights} 项
研发投入占比：{rd_ratio}
研发人员占比：{rd_team_ratio}
高新技术产品收入占比：{high_tech_income_ratio}
核心产品：{core_product}

【政策信息】
政策名称：{policy_name}
政策层级：{policy_level}
政策类别：{policy_category}
扶持内容：{policy_benefit}
硬条件诊断结果：{hard_diagnosis}
已满足硬条件：{passed_conditions}
不满足硬条件：{failed_conditions}
缺失数据：{unknown_conditions}

【软条件评估】
{soft_assessment}
优势：{strengths}
短板：{weaknesses}
培育建议：{cultivation_suggestions}

请输出以下内容的 JSON 格式：
{{
  "policy_name": "政策名称",
  "applicability": "200字以内申报可行性判断",
  "outline": [
    {{"section": "一、企业基本情况", "content": ["要点1", "要点2"]}},
    {{"section": "二、项目背景与意义", "content": ["要点1", "要点2"]}},
    {{"section": "三、技术创新与核心竞争力", "content": ["要点1", "要点2"]}},
    {{"section": "四、经济效益与社会效益", "content": ["要点1", "要点2"]}},
    {{"section": "五、附件材料清单", "content": ["要点1", "要点2"]}}
  ],
  "key_attachments": ["关键附件1", "关键附件2"],
  "gap_fill_plan": ["补齐差距1", "补齐差距2"],
  "notes": "特别提醒事项"
}}

注意：
1. 只输出 JSON，不要输出其他文字
2. 大纲内容要紧扣该政策的扶持方向和评审要点
3. 差距补齐计划要针对"不满足硬条件"和"缺失数据"给出具体可操作建议
4. 关键附件清单要列出申报时必须提交的证明材料
"""


def format_value(value: Any) -> str:
    """格式化值用于提示词"""
    if value is None:
        return "未知"
    if isinstance(value, list):
        return "、".join(str(v) for v in value) if value else "无"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def build_prompt(enterprise: Dict[str, Any], policy: Dict[str, Any], hard_result: Dict[str, Any]) -> str:
    """构建软条件打分提示词"""
    return SOFT_CONDITION_PROMPT.format(
        name=format_value(enterprise.get('name')),
        industry=format_value(enterprise.get('industry')),
        sub_industry=format_value(enterprise.get('sub_industry')),
        region=format_value(enterprise.get('region')),
        years_in_operation=format_value(enterprise.get('years_in_operation')),
        scale=format_value(enterprise.get('scale')),
        employees=format_value(enterprise.get('employees')),
        revenue=format_value(enterprise.get('revenue')),
        profit=format_value(enterprise.get('profit')),
        qualifications=format_value(enterprise.get('qualifications')),
        invention_patents=format_value(enterprise.get('invention_patents')),
        utility_models=format_value(enterprise.get('utility_models')),
        software_copyrights=format_value(enterprise.get('software_copyrights')),
        rd_ratio=format_value(enterprise.get('rd_ratio')),
        rd_team_ratio=format_value(enterprise.get('rd_team_ratio')),
        high_tech_income_ratio=format_value(enterprise.get('high_tech_income_ratio')),
        core_product=format_value(enterprise.get('core_product')),
        policy_name=format_value(policy.get('policy_name')),
        policy_level=format_value(policy.get('level')),
        policy_category=format_value(policy.get('category')),
        policy_benefit=format_value(policy.get('benefit')),
        hard_diagnosis=format_value(hard_result.get('diagnosis')),
        passed_conditions=format_value(hard_result.get('passed')),
        failed_conditions=format_value(hard_result.get('failed')),
        unknown_conditions=format_value(hard_result.get('unknown'))
    )


def build_material_prompt(enterprise: Dict[str, Any], policy: Dict[str, Any],
                         hard_result: Dict[str, Any], soft_result: Dict[str, Any]) -> str:
    """构建申报材料大纲提示词"""
    return MATERIAL_OUTLINE_PROMPT.format(
        name=format_value(enterprise.get('name')),
        industry=format_value(enterprise.get('industry')),
        sub_industry=format_value(enterprise.get('sub_industry')),
        region=format_value(enterprise.get('region')),
        years_in_operation=format_value(enterprise.get('years_in_operation')),
        scale=format_value(enterprise.get('scale')),
        employees=format_value(enterprise.get('employees')),
        revenue=format_value(enterprise.get('revenue')),
        profit=format_value(enterprise.get('profit')),
        qualifications=format_value(enterprise.get('qualifications')),
        invention_patents=format_value(enterprise.get('invention_patents')),
        utility_models=format_value(enterprise.get('utility_models')),
        software_copyrights=format_value(enterprise.get('software_copyrights')),
        rd_ratio=format_value(enterprise.get('rd_ratio')),
        rd_team_ratio=format_value(enterprise.get('rd_team_ratio')),
        high_tech_income_ratio=format_value(enterprise.get('high_tech_income_ratio')),
        core_product=format_value(enterprise.get('core_product')),
        policy_name=format_value(policy.get('policy_name')),
        policy_level=format_value(policy.get('level')),
        policy_category=format_value(policy.get('category')),
        policy_benefit=format_value(policy.get('benefit')),
        hard_diagnosis=format_value(hard_result.get('diagnosis')),
        passed_conditions=format_value(hard_result.get('passed')),
        failed_conditions=format_value(hard_result.get('failed')),
        unknown_conditions=format_value(hard_result.get('unknown')),
        soft_assessment=format_value(soft_result.get('soft_assessment')),
        strengths=format_value(soft_result.get('strengths')),
        weaknesses=format_value(soft_result.get('weaknesses')),
        cultivation_suggestions=format_value(soft_result.get('cultivation_suggestions'))
    )


def call_anthropic(prompt: str, api_key: str, model: str = "claude-3-5-sonnet-20241022") -> Optional[str]:
    """调用 Anthropic Claude API"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except ImportError:
        # 如果没有安装 anthropic SDK，使用 requests
        return call_anthropic_http(prompt, api_key, model)
    except Exception as e:
        print(f"Anthropic API 调用失败: {e}")
        return None


def call_anthropic_http(prompt: str, api_key: str, model: str = "claude-3-5-sonnet-20241022") -> Optional[str]:
    """使用 HTTP 直接调用 Anthropic API"""
    import requests
    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": model,
        "max_tokens": 2000,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except Exception as e:
        print(f"Anthropic HTTP 调用失败: {e}")
        return None


def call_openai(prompt: str, api_key: str, model: str = "gpt-4o-mini") -> Optional[str]:
    """调用 OpenAI API"""
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except ImportError:
        return call_openai_http(prompt, api_key, model)
    except Exception as e:
        print(f"OpenAI API 调用失败: {e}")
        return None


def call_openai_http(prompt: str, api_key: str, model: str = "gpt-4o-mini") -> Optional[str]:
    """使用 HTTP 直接调用 OpenAI API"""
    import requests
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenAI HTTP 调用失败: {e}")
        return None


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """解析 LLM 返回的 JSON"""
    if not response_text:
        return get_demo_result()

    # 尝试提取 JSON
    try:
        # 先尝试直接解析
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # 尝试从 markdown 代码块中提取
    import re
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试从文本中提取第一个 JSON 对象
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return get_demo_result()


def get_demo_result() -> Dict[str, Any]:
    """演示模式下的默认软条件评分结果"""
    return {
        "soft_score": 65,
        "assessment": "（演示模式）该企业属于医疗器械制造领域，产品具有一定技术含量，但公开信息有限，无法全面评估软条件。建议补充研发数据、市场证明等材料后再做精确判断。",
        "strengths": [
            "属于高新技术领域，符合政策导向",
            "已获得省级专精特新资质，具备一定竞争力"
        ],
        "weaknesses": [
            "公开信息中缺少研发投入和研发人员数据",
            "缺少市场占有率证明等软实力材料"
        ],
        "cultivation_suggestions": [
            "完善研发费用辅助账和研发人员统计",
            "准备产品技术先进性和市场占有率证明"
        ],
        "confidence": "中"
    }


def get_demo_outline() -> Dict[str, Any]:
    """演示模式下的默认申报材料大纲"""
    return {
        "policy_name": "（演示模式）",
        "applicability": "（演示模式）该企业基本符合政策申报方向，但缺少研发投入、市场占有率等关键证明材料，建议补齐后再正式申报。",
        "outline": [
            {
                "section": "一、企业基本情况",
                "content": [
                    "企业沿革、股权结构、主营业务介绍",
                    "近三年经营数据（营收、利润、纳税）",
                    "员工结构及研发人员情况"
                ]
            },
            {
                "section": "二、项目背景与意义",
                "content": [
                    "行业发展趋势与市场需求分析",
                    "项目对地方产业升级的贡献",
                    "技术突破对产业链的影响"
                ]
            },
            {
                "section": "三、技术创新与核心竞争力",
                "content": [
                    "核心技术及创新点说明",
                    "知识产权清单及技术先进性证明",
                    "与国内外同类产品对比优势"
                ]
            },
            {
                "section": "四、经济效益与社会效益",
                "content": [
                    "预期经济效益（新增营收、利润、税收）",
                    "预期社会效益（就业、环保、产业带动）",
                    "项目实施计划及里程碑"
                ]
            },
            {
                "section": "五、附件材料清单",
                "content": [
                    "营业执照、审计报告、纳税证明",
                    "知识产权证书、检测报告、用户证明",
                    "研发投入辅助账、人员社保清单"
                ]
            }
        ],
        "key_attachments": [
            "营业执照副本复印件",
            "近三年财务审计报告",
            "知识产权证书",
            "研发费用辅助账",
            "研发人员学历/社保清单",
            "产品检测报告或用户证明"
        ],
        "gap_fill_plan": [
            "完善研发费用辅助账，确保研发费占比达到政策要求",
            "补充研发人员统计数据，确保研发人员占比达标",
            "准备产品技术先进性和市场占有率证明材料"
        ],
        "notes": "演示模式：未调用真实 LLM。正式使用时请关闭演示模式并输入 API Key，以获得针对该政策的定制化大纲。"
    }


def score_soft_conditions(enterprise: Dict[str, Any], policy: Dict[str, Any],
                         hard_result: Dict[str, Any], provider: str = "anthropic",
                         api_key: Optional[str] = None, use_demo: bool = False) -> Dict[str, Any]:
    """
    对单条政策进行软条件打分

    参数：
        enterprise: 企业画像
        policy: 政策信息
        hard_result: 硬条件诊断结果
        provider: LLM 提供商，anthropic 或 openai
        api_key: API 密钥
        use_demo: 是否使用演示模式

    返回：
        软条件评分结果字典
    """
    if use_demo or not api_key:
        result = get_demo_result()
        result["provider"] = "demo"
        result["raw_response"] = "演示模式，未调用真实 LLM"
        return result

    prompt = build_prompt(enterprise, policy, hard_result)

    if provider == "anthropic":
        response_text = call_anthropic(prompt, api_key)
    elif provider == "openai":
        response_text = call_openai(prompt, api_key)
    else:
        return get_demo_result()

    result = parse_llm_response(response_text)
    result["provider"] = provider
    result["raw_response"] = response_text
    return result


def generate_material_outline(enterprise: Dict[str, Any], policy: Dict[str, Any],
                             hard_result: Dict[str, Any], soft_result: Dict[str, Any],
                             provider: str = "anthropic", api_key: Optional[str] = None,
                             use_demo: bool = False) -> Dict[str, Any]:
    """
    为单条政策生成申报材料大纲

    参数：
        enterprise: 企业画像
        policy: 政策信息
        hard_result: 硬条件诊断结果
        soft_result: 软条件评估结果
        provider: LLM 提供商
        api_key: API 密钥
        use_demo: 是否使用演示模式

    返回：
        申报材料大纲字典
    """
    if use_demo or not api_key:
        result = get_demo_outline()
        result["provider"] = "demo"
        result["raw_response"] = "演示模式，未调用真实 LLM"
        return result

    prompt = build_material_prompt(enterprise, policy, hard_result, soft_result)

    if provider == "anthropic":
        response_text = call_anthropic(prompt, api_key)
    elif provider == "openai":
        response_text = call_openai(prompt, api_key)
    else:
        return get_demo_outline()

    if not response_text:
        result = get_demo_outline()
        result["provider"] = "error"
        result["raw_response"] = "LLM 调用失败，返回演示模式大纲"
        return result

    result = parse_llm_response(response_text)
    result["provider"] = provider
    result["raw_response"] = response_text
    return result


def combine_scores(hard_result: Dict[str, Any], soft_result: Dict[str, Any],
                   hard_weight: float = 0.6, soft_weight: float = 0.4) -> Dict[str, Any]:
    """
    综合硬条件分数和软条件分数
    """
    hard_score = hard_result.get('match_score', 0)
    soft_score = soft_result.get('soft_score', 0)

    # 如果硬条件有明显不满足，软条件分数权重降低
    if hard_result.get('failed_count', 0) > 2:
        hard_weight = 0.8
        soft_weight = 0.2

    combined_score = int(hard_score * hard_weight + soft_score * soft_weight)

    return {
        "combined_score": combined_score,
        "hard_score": hard_score,
        "soft_score": soft_score,
        "hard_weight": hard_weight,
        "soft_weight": soft_weight
    }
