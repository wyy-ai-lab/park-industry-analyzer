"""
综合诊断模块
整合硬条件匹配和 LLM 软条件打分
"""

import os
from typing import Dict, List, Any, Optional

from .matcher import run_diagnosis
from .llm_scorer import score_soft_conditions, combine_scores


def load_env_file(env_path: str = ".env") -> None:
    """手动加载 .env 文件（不依赖 python-dotenv）"""
    if not os.path.exists(env_path):
        return

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()


# 启动时加载环境变量
load_env_file()


def get_api_config() -> Dict[str, Any]:
    """获取 API 配置"""
    provider = os.getenv('LLM_PROVIDER', 'anthropic')
    api_key = None

    if provider == 'anthropic':
        api_key = os.getenv('ANTHROPIC_API_KEY')
    elif provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')

    use_demo = os.getenv('USE_DEMO_MODE', 'false').lower() == 'true'

    return {
        "provider": provider,
        "api_key": api_key,
        "use_demo": use_demo or not api_key
    }


def run_enhanced_diagnosis(enterprise: Dict[str, Any], policies: List[Dict[str, Any]],
                          provider: Optional[str] = None,
                          api_key: Optional[str] = None,
                          use_demo: bool = False,
                          max_policies_for_soft_score: int = 5) -> Dict[str, Any]:
    """
    运行增强版诊断：硬条件 + 软条件

    参数：
        enterprise: 企业画像
        policies: 政策列表
        provider: LLM 提供商
        api_key: API 密钥
        use_demo: 是否使用演示模式
        max_policies_for_soft_score: 对多少条政策进行软条件打分（控制成本）

    返回：
        包含硬条件和软条件的综合诊断结果
    """
    # 先运行硬条件诊断
    diagnosis_result = run_diagnosis(enterprise, policies)

    # 如果没有配置，尝试从环境变量读取
    config = get_api_config()
    if provider is None:
        provider = config['provider']
    if api_key is None:
        api_key = config['api_key']
    if not use_demo:
        use_demo = config['use_demo']

    # 选择最值得做软条件打分的政策
    # 优先级：培育申报 > 立即申报 > 持续关注 > 暂不适合
    priority_order = {"培育申报": 0, "立即申报": 1, "持续关注": 2, "暂不适合": 3}
    sorted_results = sorted(
        diagnosis_result['results'],
        key=lambda x: (priority_order.get(x['diagnosis'], 99), -x['match_score'])
    )

    # 对前 N 条政策进行软条件打分
    policies_for_soft_score = sorted_results[:max_policies_for_soft_score]

    # 建立 policy_id 到 policy 的映射
    policy_map = {p['policy_id']: p for p in policies}

    for result in policies_for_soft_score:
        policy_id = result['policy_id']
        policy = policy_map.get(policy_id, {})

        # 调用 LLM 进行软条件打分
        soft_result = score_soft_conditions(
            enterprise=enterprise,
            policy=policy,
            hard_result=result,
            provider=provider,
            api_key=api_key,
            use_demo=use_demo
        )

        # 综合硬条件和软条件分数
        combined = combine_scores(result, soft_result)

        # 更新结果
        result['soft_score'] = soft_result['soft_score']
        result['soft_assessment'] = soft_result['assessment']
        result['strengths'] = soft_result['strengths']
        result['weaknesses'] = soft_result['weaknesses']
        result['cultivation_suggestions'] = soft_result['cultivation_suggestions']
        result['confidence'] = soft_result['confidence']
        result['combined_score'] = combined['combined_score']
        result['hard_score'] = combined['hard_score']
        result['soft_weight'] = combined['soft_weight']
        result['llm_provider'] = soft_result.get('provider', 'unknown')

    # 对未做软条件打分的政策，设置默认值
    for result in diagnosis_result['results']:
        if 'combined_score' not in result:
            result['combined_score'] = result['match_score']
            result['hard_score'] = result['match_score']
            result['soft_score'] = None
            result['soft_assessment'] = "未进行软条件评估"
            result['strengths'] = []
            result['weaknesses'] = []
            result['cultivation_suggestions'] = []
            result['confidence'] = "未评估"
            result['llm_provider'] = "none"

    # 按综合分数重新排序
    diagnosis_result['results'].sort(key=lambda x: -x['combined_score'])

    # 添加配置信息
    diagnosis_result['llm_config'] = {
        "provider": provider,
        "use_demo": use_demo,
        "max_policies_for_soft_score": max_policies_for_soft_score
    }

    return diagnosis_result
