"""
产业智能梳理引擎
================
面向园区的"材料 → 洞察"主链路：

1. 产业分类    ：从企业目录/文字材料中识别企业，归类到产业方向
2. 环节梳理    ：将企业归位到产业上中下游的具体环节
3. 强弱缺失分析：统计环节分布，识别薄弱环节与断点
4. 路径建议    ：生成强链 / 补链 / 延链优化路径
5. 招商清单    ：按目标区域生成环节对应的招商目标企业清单
6. 产业资源    ：梳理对应的研究院、协会等产业资源

LLM 可用时走 LLM 结构化抽取；无 API Key 时自动降级为模板模式
（模板模式只对材料做行解析与关键词归位，缺失判定与目标企业生成
需要 LLM 的产业知识，模板模式会明确标注"待 LLM 生成"）。
"""

import json
import os
import re
from typing import Dict, List, Any, Optional

from .park_llm import (
    _call_anthropic, _call_openai, _parse_llm_response,
    get_llm_config, get_llm_error, clear_llm_error,
)


# ---------------------------------------------------------------- LLM 开关

def _llm_available() -> Optional[str]:
    """返回可用 provider 名称（anthropic/openai），不可用返回 None。
    配置来源：Streamlit Secrets 优先，环境变量兜底。"""
    cfg = get_llm_config()
    return cfg["provider"] if cfg["api_key"] else None


def _llm_call(prompt: str) -> Optional[Dict[str, Any]]:
    provider = _llm_available()
    if not provider:
        return None
    cfg = get_llm_config()
    text = _call_anthropic(prompt, cfg["api_key"], cfg["model"]) \
        if provider == "anthropic" else _call_openai(prompt, cfg["api_key"], cfg["model"], cfg["base_url"])
    return _parse_llm_response(text) or None


# ---------------------------------------------------------------- 阶段1：产业分类

CLASSIFY_PROMPT = """你是一位资深的产业研究专家。请从以下园区材料（企业目录、简介文字等）中识别每一家企业，
将其归类到产业方向和主营业务，输出 JSON：

{{
  "industries": [
    {{
      "industry": "产业方向（如：新材料、高端装备、生物医药）",
      "enterprises": [
        {{"name": "企业名称", "products": "主要产品", "tech": "核心技术/工艺", "scale": "规模描述"}}
      ]
    }}
  ]
}}

材料：
```
{material}
```

{focus_hint}
注意：
1. 只输出 JSON；每家企业必须出现在结果中，不得遗漏
2. 产业方向控制在 1-3 个，主线产业放第一位
3. products/tech/scale 材料中没有的填 "未提及"，不要编造
"""


def _classify_llm(material: str, focus_hint: str) -> Optional[Dict[str, Any]]:
    hint = f"用户提示园区主攻方向为「{focus_hint}」，分类时优先考虑。" if focus_hint else ""
    return _llm_call(CLASSIFY_PROMPT.format(material=material[:8000], focus_hint=hint))


# 模板模式关键词归位（跨产业通用，仅按字面判断）
_SEGMENT_KEYWORDS = [
    ("原材料", ["原材料", "材料", "母粒", "基材", "单体", "树脂", "粉末"]),
    ("核心部件/组件", ["部件", "组件", "零件", "模组", "器件", "电芯", "芯片", "传感器"]),
    ("生产制造", ["制造", "生产", "加工", "组装", "整机", "设备", "装备"]),
    ("系统集成/平台", ["系统", "集成", "平台", "解决方案", "整机"]),
    ("应用与运营服务", ["运营", "服务", "应用", "销售", "租赁", "回收", "检测", "物流"]),
]

_LAYER_OF_SEGMENT = {
    "原材料": "上游", "核心部件/组件": "中游",
    "生产制造": "中游", "系统集成/平台": "中下游",
    "应用与运营服务": "下游", "其他": "待定",
}


def _classify_template(material: str, focus_hint: str) -> Dict[str, Any]:
    """模板模式：按行解析企业（含名称与简介拆分），关键词猜测产业环节"""
    name_markers = ("公司", "厂", "集团", "中心", "院", "研究所", "工作室")
    enterprises = []
    for line in material.splitlines():
        line = line.strip().lstrip("•·-0123456789.、）)")
        if len(line) < 4 or not any(m in line for m in name_markers):
            continue  # 跳过标题行、空行、非企业行
        parts = re.split(r"[—\-–]|：|: {1}", line, maxsplit=1)
        name = re.split(r"[，,（(]", parts[0])[0].strip()
        products = parts[1].split("，")[0].strip(" ，。") if len(parts) > 1 else "未提及"
        if not name or len(name) > 30:
            continue
        enterprises.append({"name": name, "products": products,
                            "tech": "未提及", "scale": "未提及"})
    # 去重保序
    seen, unique = set(), []
    for e in enterprises:
        if e["name"] not in seen:
            seen.add(e["name"])
            unique.append(e)
    industry = focus_hint or "待确认（模板模式建议填写产业方向）"
    return {"industries": [{"industry": industry, "enterprises": unique}]}


# ---------------------------------------------------------------- 阶段2：环节梳理

CHAIN_PROMPT = """你是一位产业链规划专家。已知园区企业分类如下：
{classification}

请构建该主导产业的上中下游环节图谱，把每家企业归位到具体环节，输出 JSON：
{{
  "segments": [
    {{
      "layer": "上游/中游/下游",
      "segment": "环节名称（尽量细，如"正极材料"、"驱动电机"、"运营服务"）",
      "enterprises": ["企业名称，与输入一致"],
      "note": "该环节一句话说明"
    }}
  ]
}}

要求：
1. 只输出 JSON；每家企业都必须出现在某个环节，不得遗漏
2. 没有企业覆盖的环节也要列出（enterprises 为空数组），用于识别缺失
3. 上中下游划分以产业常识为准
"""


def _build_chain_llm(classification: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return _llm_call(CHAIN_PROMPT.format(
        classification=json.dumps(classification, ensure_ascii=False)[:6000]))


def _build_chain_template(classification: Dict[str, Any]) -> Dict[str, Any]:
    """模板模式：关键词归位，无法识别缺失环节"""
    segments: Dict[str, Dict[str, Any]] = {}
    for group in classification.get("industries", []):
        for ent in group.get("enterprises", []):
            text = f"{ent.get('name', '')} {ent.get('products', '')}"
            seg_name = "其他"
            for seg, kws in _SEGMENT_KEYWORDS:
                if any(k in text for k in kws):
                    seg_name = seg
                    break
            seg = segments.setdefault(seg_name, {
                "layer": _LAYER_OF_SEGMENT.get(seg_name, "待定"),
                "segment": seg_name, "enterprises": [], "note": "模板模式按关键词归位"})
            seg["enterprises"].append(ent.get("name", ""))
    return {"segments": list(segments.values()), "_template": True}


# ---------------------------------------------------------------- 阶段3：强弱缺失

def analyze_gaps(chain_map: Dict[str, Any]) -> Dict[str, Any]:
    """基于环节图谱做规则化强弱缺失分析（LLM/模板模式通用）"""
    segments = chain_map.get("segments", [])
    layer_counts: Dict[str, int] = {"上游": 0, "中游": 0, "下游": 0}
    weak, empty = [], []

    for seg in segments:
        n = len(seg.get("enterprises", []))
        layer = seg.get("layer", "待定")
        if layer in layer_counts:
            layer_counts[layer] += n
        if n == 0:
            empty.append(seg.get("segment", ""))
        elif n == 1:
            weak.append(seg.get("segment", ""))

    total = sum(layer_counts.values()) or 1
    return {
        "layer_counts": layer_counts,
        "layer_ratio": {k: round(v / total * 100, 1) for k, v in layer_counts.items()},
        "weak_segments": weak,
        "empty_segments": empty,
        "is_template": bool(chain_map.get("_template")),
    }


# ---------------------------------------------------------------- 阶段4：路径建议

PATHS_PROMPT = """你是园区产业规划专家。基于以下产业链环节分析，为园区生成"强链、补链、延链"优化路径，输出 JSON：
{{
  "strengthen": [{{"segment": "环节", "action": "具体动作", "rationale": "依据"}}],
  "complete":   [{{"segment": "目标环节", "action": "具体动作", "rationale": "依据"}}],
  "extend":     [{{"direction": "延伸方向", "action": "具体动作", "rationale": "依据"}}]
}}

要求：每条 1-2 句、可落地；complete 优先缺失环节（不超过3条）；extend 指向高附加值延伸（不超过2条）。

【产业分类】{classification}
【环节分布】{chain}
【强弱缺失】{gaps}
"""


def _paths_llm(classification: Dict[str, Any], chain_map: Dict[str, Any],
               gaps: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return _llm_call(PATHS_PROMPT.format(
        classification=json.dumps(classification, ensure_ascii=False)[:3000],
        chain=json.dumps(chain_map.get("segments", []), ensure_ascii=False)[:3000],
        gaps=json.dumps({k: gaps[k] for k in ("weak_segments", "empty_segments", "layer_ratio")},
                        ensure_ascii=False),
    ))


def _paths_template(gaps: Dict[str, Any]) -> Dict[str, Any]:
    weak = gaps.get("weak_segments", [])
    empty = gaps.get("empty_segments", [])
    strengthen = [{"segment": s, "action": f"支持现有{s}企业技改扩产、引入二家以上形成竞争配套",
                   "rationale": "环节已有布局但仅单一企业，抗风险与议价能力弱"} for s in weak[:3]]
    complete = [{"segment": s, "action": f"将{s}列入招商补链目标，定向招引龙头企业落地",
                 "rationale": "园区该环节尚无企业布局"} for s in empty[:3]]
    extend = [{"direction": "下游应用与服务延伸",
               "action": "围绕现有产品向应用场景、运营服务、后市场延伸，提升本地增值率",
               "rationale": "下游应用环节通常投资轻、见效快，可就地消化中游产能"}]
    return {"strengthen": strengthen, "complete": complete, "extend": extend,
            "_template": True}


# ---------------------------------------------------------------- 阶段5：招商目标企业

TARGETS_PROMPT = """你是招商情报专家。针对以下园区缺失/薄弱的产业环节，生成目标招商企业清单，输出 JSON：
{{
  "targets": [
    {{
      "name": "目标企业名称（真实存在的知名企业）",
      "segment": "对应环节",
      "region": "企业当前所在地（城市）",
      "reason": "与园区现有企业的配套逻辑，1-2 句",
      "signal": "落地线索（扩产计划/区域布局/供应链合作等）"
    }}
  ]
}}

【产业方向】{industry}
【目标招商区域偏好】{region}
【缺失环节】{empty}
【薄弱环节】{weak}

要求：只输出 JSON；每类环节给 2 家；优先选择与园区现有企业有明确配套关系、
且公开信息可见扩张意愿的企业；region 优先用户指定区域及其周边。
"""


def _targets_llm(industry: str, region: str, gaps: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    result = _llm_call(TARGETS_PROMPT.format(
        industry=industry,
        region=region or "不限（全国）",
        empty="、".join(gaps.get("empty_segments", [])) or "无",
        weak="、".join(gaps.get("weak_segments", [])) or "无",
    ))
    return (result or {}).get("targets")


# ---------------------------------------------------------------- 阶段6：产业资源

RESOURCES_PROMPT = """你是产业资源顾问。针对产业方向「{industry}」，梳理可对接的研究机构与行业组织，输出 JSON：
{{
  "institutes": [{{"name": "研究院/实验室名称", "location": "所在地", "focus": "与园区可合作的方向"}}],
  "associations": [{{"name": "协会/联盟名称", "focus": "可借助的作用（标准、展会、上下游对接）"}}]
}}

要求：只输出 JSON；各给 3-5 个，优先国内该产业有影响力的机构；不要编造不存在的机构。
"""


def _resources_llm(industry: str) -> Optional[Dict[str, Any]]:
    if not industry or industry.startswith("待确认"):
        return None
    return _llm_call(RESOURCES_PROMPT.format(industry=industry))


# ---------------------------------------------------------------- 本地行业知识库

_KB_CACHE: Dict[str, Any] = {}


def _load_kb(file_path: str) -> Dict[str, Any]:
    """加载本地知识库（带进程内缓存）"""
    if file_path not in _KB_CACHE:
        import os
        if not os.path.exists(file_path):
            _KB_CACHE[file_path] = {}
        else:
            with open(file_path, encoding="utf-8") as f:
                _KB_CACHE[file_path] = json.load(f)
    return _KB_CACHE[file_path]


def _match_industry_key(industries: Dict[str, Any], industry: str) -> Optional[str]:
    """产业方向模糊匹配知识库键（精确 → 包含 → 被包含）"""
    if not industry or industry.startswith("待确认"):
        return None
    if industry in industries:
        return industry
    for key in industries:
        if industry in key or key in industry:
            return key
    return None


def _resolve_kb_key(industries: Dict[str, Any], industry: str,
                    corpus_text: str = "") -> Optional[str]:
    """匹配知识库产业键；industry 未命中时回退到从材料全文中识别（如标题含"锂电新材料"）"""
    key = _match_industry_key(industries, industry)
    if key:
        return key
    for k in industries:
        if k in corpus_text:
            return k
    return None


def kb_targets(industry: str, corpus_text: str) -> List[Dict[str, Any]]:
    """
    从本地知识库检索招商目标企业。
    corpus_text：环节名 + 企业产品描述等全部文本，用于包含匹配环节键。
    命中结果标注 source=知识库。
    """
    kb = _load_kb("data/invest_targets.json").get("industries", {})
    key = _resolve_kb_key(kb, industry, corpus_text)
    if not key:
        return []
    hits = []
    for segment, companies in kb[key].items():
        if segment in corpus_text:
            for c in companies:
                hits.append({"segment": segment, "source": "知识库",
                             **{k: c.get(k, "") for k in ("name", "region", "reason", "signal")}})
    return hits


def kb_resources(industry: str, corpus_text: str = "") -> Dict[str, Any]:
    """从本地知识库检索研究院/协会资源；industry 未命中时回退到材料全文识别"""
    kb = _load_kb("data/industry_resources.json").get("industries", {})
    key = _resolve_kb_key(kb, industry, corpus_text)
    if not key:
        return {}
    return kb[key]


# ---------------------------------------------------------------- 主编排

def run_industry_analysis(material: str, focus_hint: str = "",
                          region: str = "", local_only: bool = False) -> Dict[str, Any]:
    """
    运行完整产业梳理流程。

    local_only=True 时强制本地模板模式：不调用任何外部 LLM，
    材料不会发生出域，适用于涉密/敏感材料场景。

    返回结构：
    {
      "mode": "llm" | "template",
      "classification": {...},      # 阶段1
      "chain_map": {...},           # 阶段2
      "gaps": {...},                # 阶段3
      "paths": {...},               # 阶段4
      "targets": [...],             # 阶段5（模板模式为空）
      "resources": {...},           # 阶段6（模板模式为空）
    }
    """
    llm_on = not local_only and _llm_available() is not None
    clear_llm_error()

    # 阶段1：产业分类
    classification = _classify_llm(material, focus_hint) if llm_on else None
    if not classification or not classification.get("industries"):
        classification = _classify_template(material, focus_hint)

    # 阶段2：环节梳理
    chain_map = _build_chain_llm(classification) if llm_on else None
    if not chain_map or not chain_map.get("segments"):
        chain_map = _build_chain_template(classification)

    # 阶段3：强弱缺失（规则计算，两种模式通用）
    gaps = analyze_gaps(chain_map)

    # 阶段4：路径建议
    paths = _paths_llm(classification, chain_map, gaps) if llm_on else None
    if not paths:
        paths = _paths_template(gaps)

    # 阶段5：招商目标——本地知识库（已核实）打底，LLM 补全（待核实）
    industry_main = classification["industries"][0]["industry"] if classification.get("industries") else ""
    corpus_text = " ".join(
        [s.get("segment", "") for s in chain_map.get("segments", [])]
        + [e.get("products", "") for g in classification.get("industries", [])
           for e in g.get("enterprises", [])]
        + [material[:2000]]
    )
    targets = kb_targets(industry_main, corpus_text)
    seen_names = {t["name"] for t in targets}
    if llm_on:
        for t in (_targets_llm(industry_main, region, gaps) or []):
            if t.get("name") and t["name"] not in seen_names:
                seen_names.add(t["name"])
                targets.append({"source": "AI生成", **t})

    # 阶段6：产业资源——知识库优先，LLM 补充库外产业
    resources = kb_resources(industry_main, corpus_text)
    if not resources and llm_on:
        resources = _resources_llm(industry_main) or {}

    result = {
        "mode": "llm" if llm_on else "template",
        "classification": classification,
        "chain_map": chain_map,
        "gaps": gaps,
        "paths": paths,
        "targets": targets or [],
        "resources": resources or {},
        "focus_hint": focus_hint,
        "region": region,
        "local_only": local_only,
    }
    # LLM 已配置但各阶段均未能产出 → 页面需要显式提示降级原因
    if llm_on and get_llm_error():
        result["llm_error"] = get_llm_error()
    return result


def _report_summary(result: Dict[str, Any]) -> List[str]:
    """报告摘要要点（Markdown / Word / PDF 共用）"""
    from datetime import datetime
    all_ents = [e for g in result["classification"].get("industries", [])
                for e in g.get("enterprises", [])]
    segments = result["chain_map"].get("segments", [])
    gaps = result.get("gaps", {})
    n_weak = len(gaps.get("weak_segments", []))
    n_empty = len(gaps.get("empty_segments", []))
    paths = result.get("paths", {})
    n_kb = sum(1 for t in result.get("targets", []) if t.get("source") == "知识库")
    n_ai = len(result.get("targets", [])) - n_kb

    mode = "LLM 智能梳理" if result.get("mode") == "llm" else "本地模板模式"
    lines = [
        f"- 编制日期：{datetime.now().strftime('%Y年%m月%d日')}；生成模式：{mode}",
        f"- 本次梳理共识别企业 **{len(all_ents)}** 家，覆盖产业链环节 **{len(segments)}** 个"
        f"（上游 {sum(1 for s in segments if s.get('layer') == '上游')} / "
        f"中游 {sum(1 for s in segments if s.get('layer') == '中游')} / "
        f"下游 {sum(1 for s in segments if s.get('layer') == '下游')}）。",
        f"- 诊断出薄弱环节 **{n_weak}** 个、缺失环节 **{n_empty}** 个，"
        f"据此生成强链建议 {len(paths.get('strengthen', []))} 条、"
        f"补链建议 {len(paths.get('complete', []))} 条、延链建议 {len(paths.get('extend', []))} 条。",
    ]
    if result.get("targets"):
        lines.append(f"- 输出招商目标企业 **{len(result['targets'])}** 家"
                     f"（知识库已核实 {n_kb} 家" +
                     (f"，AI 生成待核实 {n_ai} 家）" if n_ai else "）"))
    if result.get("region"):
        lines.append(f"- 园区背景：{result['region']}")
    return lines


def _report_disclaimer(result: Dict[str, Any]) -> str:
    mode = "LLM 智能梳理" if result.get("mode") == "llm" else "本地模板模式（仅规则归位结果）"
    return (f"本报告由「园区产业分析智能体」生成（{mode}），供园区产业研究与招商工作内部参考。"
            "招商目标清单中 AI 生成条目基于公开信息整理，企业名称、所在地与落地线索请在正式对接前逐一人工核实；"
            "知识库条目虽经人工整理，仍建议联系前复核最新动态。")


def to_markdown(result: Dict[str, Any]) -> str:
    """导出梳理结果为 Markdown 报告"""
    lines = ["# 园区产业梳理报告", ""]
    lines.extend(_report_summary(result))
    lines.append("")

    # 产业分类
    lines.append("## 一、产业分类")
    for group in result["classification"].get("industries", []):
        lines.append(f"### {group['industry']}")
        for e in group.get("enterprises", []):
            desc = "、".join(x for x in (e.get("products"), e.get("tech")) if x and x != "未提及")
            lines.append(f"- **{e['name']}**{('：' + desc) if desc else ''}")
    lines.append("")

    # 环节梳理
    lines.append("## 二、上中下游环节梳理")
    for layer in ("上游", "中游", "下游"):
        lines.append(f"### {layer}")
        segs = [s for s in result["chain_map"].get("segments", []) if s.get("layer") == layer]
        if not segs:
            lines.append("- （无企业布局）")
        for s in segs:
            names = "、".join(s.get("enterprises", [])) or "（缺失）"
            lines.append(f"- **{s['segment']}**：{names}")
    lines.append("")

    # 路径建议
    lines.append("## 三、强链补链延链路径")
    paths = result.get("paths", {})
    for title, key in (("🔧 强链", "strengthen"), ("🧩 补链", "complete"), ("➡️ 延链", "extend")):
        lines.append(f"### {title}")
        for item in paths.get(key, []):
            seg = item.get("segment") or item.get("direction", "")
            lines.append(f"- **{seg}**：{item.get('action', '')}（{item.get('rationale', '')}）")
    lines.append("")

    # 招商目标
    lines.append("## 四、招商目标企业清单")
    if result.get("targets"):
        lines.append("| 企业 | 环节 | 所在地 | 配套逻辑 | 落地线索 | 来源 |")
        lines.append("|---|---|---|---|---|---|")
        for t in result["targets"]:
            src = "知识库·已核实" if t.get("source") == "知识库" else "AI生成·待核实"
            lines.append(f"| {t.get('name','')} | {t.get('segment','')} | {t.get('region','')} "
                         f"| {t.get('reason','')} | {t.get('signal','')} | {src} |")
        lines.append("")
        lines.append("> ⚠️ AI 生成条目对接前请逐一核实企业真实性与落地意愿；知识库条目已人工整理，仍建议联系前复核。")
    else:
        lines.append("（未命中知识库且未配置 API Key；维护 data/invest_targets.json 知识库或配置 Key 后输出清单）")
    lines.append("")

    # 产业资源
    lines.append("## 五、研究院 / 协会资源")
    res = result.get("resources", {})
    if res:
        lines.append("### 研究机构")
        for i in res.get("institutes", []):
            lines.append(f"- **{i.get('name','')}**（{i.get('location','')}）：{i.get('focus','')}")
        lines.append("### 行业组织")
        for a in res.get("associations", []):
            lines.append(f"- **{a.get('name','')}**：{a.get('focus','')}")
    else:
        lines.append("（模板模式未生成；配置 API Key 后自动输出机构清单）")

    lines += ["", "## 六、使用说明", "", _report_disclaimer(result), ""]
    return "\n".join(lines)
