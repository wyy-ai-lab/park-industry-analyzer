# 园区产业分析智能体

基于 Streamlit 的「园区产业分析智能体」演示项目，打通**政策—产业—企业**三层链路。当前以**合肥高新区新能源汽车产业园**为演示场景，提供园区产业概览、产业地图、产业链图谱、企业透视、发展建议以及单个企业政策诊断辅导能力。

## 功能特性

1. **园区概览**：核心指标卡片、产业分布、头部企业、企业梯队与产业链层级
2. **产业地图**：产业领域分布、企业梯队金字塔、创新密度分析、主导产业识别
3. **产业链图谱**：产业链完整度、本地配套率、环节强弱缺失与断链风险、补链建议
4. **企业透视**：50 家演示企业搜索、筛选、下钻，一键加载企业画像并进入诊断
5. **发展建议**：基于园区指标生成结构化诊断结论、招商补链与企业培育建议（LLM / 模板双模式）
6. **企业诊断辅导**：支持企业画像、政策诊断、报告导出、培育路线图

## 目录结构

```
park-industry-analyzer/
├── app.py                          # 产品首页
├── pages/
│   ├── 1_园区概览.py               # 园区概览
│   ├── 2_产业地图.py               # 产业地图
│   ├── 3_产业链图谱.py             # 产业链图谱
│   ├── 4_企业透视.py               # 企业透视
│   ├── 5_发展建议.py               # 发展建议
│   └── 6_企业诊断辅导.py           # 单个企业政策诊断辅导
├── engine/
│   ├── __init__.py
│   ├── ui_helpers.py               # Apple 风格主题与 UI 组件
│   ├── park_metrics.py             # 园区指标计算
│   ├── park_charts.py              # 园区可视化图表
│   ├── park_llm.py                 # 园区 LLM 诊断
│   ├── industry_classifier.py      # 产业标签分类
│   ├── chain_position.py           # 产业链位置与强弱环节
│   ├── matcher.py                  # 企业政策硬条件匹配
│   ├── diagnosis.py                # 企业综合诊断编排
│   ├── llm_scorer.py               # LLM 软条件打分
│   ├── radar_chart.py              # 企业能力雷达图
│   ├── report_export.py            # 报告导出 Markdown/Word/PDF
│   ├── dashboard.py                # 诊断结果看板
│   └── cultivation_roadmap.py      # 培育路线图
├── data/
│   ├── park_enterprises.json       # 50 家演示园区企业数据
│   ├── enterprise.json             # 单个企业画像（示例）
│   ├── policies.json               # 示例政策库
│   └── cases/                      # 企业画像案例
├── .streamlit/
│   └── config.toml                 # Streamlit 主题与配置
├── requirements.txt
├── .env.example                    # API Key 配置模板
└── README.md
```

## 安装依赖

```bash
cd park-industry-analyzer
pip install -r requirements.txt
```

## 运行应用

```bash
python -m streamlit run app.py
```

运行后浏览器会自动打开 `http://localhost:8501`。

## 使用步骤

1. **查看园区概览**：了解合肥高新区新能源汽车产业园的整体情况
2. **产业地图**：查看产业分布、企业梯队与创新密度
3. **产业链图谱**：识别强势、薄弱、缺失与风险环节
4. **企业透视**：搜索/筛选企业，点击「进入该企业政策诊断辅导」加载画像
5. **发展建议**：查看园区级诊断结论与招商、培育、政策建议
6. **企业诊断辅导**：
   - 在「企业画像」标签页确认或修改企业信息并保存
   - 在「政策诊断」标签页运行诊断
   - 在「诊断报告」标签页查看雷达图、TOP3 政策并导出 Word/PDF
   - 在「培育路线图」标签页查看分阶段培育动作

## 演示数据说明

`data/park_enterprises.json` 包含 50 家 fictitious 企业，覆盖：

- **产业领域**：动力电池、电机电控、智能网联、整车制造、充换电设施、汽车服务、其他配套
- **企业角色**：链主企业 3 家、骨干企业 7 家、高新技术企业 16 家、科技型中小企业 14 家、配套服务企业 10 家
- **产业链层级**：上游原材料/核心材料、中游核心制造/关键平台、下游终端应用/运营服务

## LLM 配置（可选）

如需使用真实 LLM 生成园区诊断或企业软条件评估：

1. 复制 `.env.example` 为 `.env`
2. 填入 `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY`
3. 在对应页面关闭演示模式或保持默认（无 Key 时自动使用模板/演示模式）

## 在线访问

项目已部署至 Streamlit Cloud：

👉 **`https://park-industry-analyzer.streamlit.app`**

## 在线部署（Streamlit Cloud）

1. 将本项目内容推送到 GitHub 仓库（仓库根目录包含 `app.py`、`pages/`、`engine/` 等）
2. 访问 [Streamlit Community Cloud](https://streamlit.io/cloud)，用 GitHub 账号登录
3. 点击 **New app**，选择仓库、分支（main）和 Main file path（`app.py`）
4. 若使用真实 LLM，请在 **Settings → Secrets** 中添加：

```toml
ANTHROPIC_API_KEY = "your-key"
OPENAI_API_KEY = "your-key"
```

5. 点击 **Deploy**，等待 1-2 分钟即可获得在线链接

## 后续优化方向

1. 接入真实园区与企业数据
2. 扩展政策库并支持动态抓取
3. 产业链图谱增加企业间供需关系网络图
4. 多园区对比与产业迁移分析
5. 诊断报告模板与企业画像字段的行业化定制

## 相关笔记

- 本项目为「园区产业分析智能体」的演示项目，远期将扩展为「政策-产业-企业」三层产品体系
