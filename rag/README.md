# 中医问诊辅助 RAG 系统

这是一个面向中医健康咨询场景的本地问诊辅助系统原型。项目基于结构化中医知识库，提供候选证型检索、多轮问诊追问、红旗症状安全分流和 Streamlit Web 演示。

> 本项目仅用于学习、展示和工程实践，不提供医学诊断或处方。方剂信息仅作传统知识参考，不能作为自行用药依据。

## 2026-10 新增能力（结题演示版）

- 多症状组合匹配：一次输入多个症状，按“症状覆盖度 + 检索相关度”加权排序。
- 同义词与轻微错别字容错：支持“发烧/发热”“怕冷/畏寒”“咽通→咽痛”等常见表达。
- 来源可追溯知识库模式：使用 20 条带 `source_title`、`source_url`、`source_locator`、`review_status` 的记录。
- 可选大模型生成（OpenAI 兼容，默认 DeepSeek，可切换 Kimi / 通义千问）：密钥走环境变量或项目 `.env` 文件；含超时重试、温度自适应、RAG 引用校验（提及检索之外的证型会先自动重试纠正，仍不合格才回退本地模板）与安全过滤；方剂名称必须来自检索上下文。
- 结构化问诊报告：候选方向、依据、来源、审核状态、建议追问、调理方向参考、传统知识参考（方剂名称 + 强制免责声明）七段式输出；CLI 可导出 Markdown，网页可下载。
- 大模型槽位增强（可选）：用大模型把自由文本回答抽取为结构化槽位，失败自动回退规则抽取。
- 大模型可插拔：内置 DeepSeek / Kimi / 通义千问预设，网页端可直接切换厂商与模型（支持从厂商拉取可用模型列表），命令行支持 `--provider` 与 `--model`。
- 2026-10-22 前端重构：采用米白/青绿主题，增加动态来源状态、阳性与否定线索区分、Top 3 候选卡片、原生来源展开和移动端单列布局；红旗状态停止显示候选方向。
- 红旗症状与低置信度不调用大模型：优先安全分流或提示信息不足。
- 自建 40 条准确率评测：覆盖知识库改写、口语化改写、错别字、红旗、否定表达和低置信度；结果如实输出，不代表临床准确率。
- 本地 SHA-256 哈希链存证：可追加记录、校验链完整性、检测篡改，并提供可复跑的存证自检。

运行新增能力：

```bash
python -m tcm_agent.cli --demo
python -m tcm_agent.cli --demo --kb-mode sourced --llm --llm-max-tokens 256
python -m tcm_agent.cli --demo --kb-mode sourced --llm --llm-slots --report-out reports/consultation.md
python tests/evaluate_query_understanding.py
python tests/evaluate_source_backed.py
python tests/evaluate_llm_generation.py
python tests/evaluate_llm_generation.py --live
python tests/evaluate_accuracy.py
python tests/evaluate_ledger.py
python -m tcm_agent.cli --demo --ledger data/local_ledger_demo.json
python -m tcm_agent.cli --verify-ledger data/local_ledger_demo.json
```

运行命令速查见 `docs/RUNBOOK.md`；提交包内的统一运行入口是 `../运行说明_提交版.md`。

## 项目亮点

- 结构化中医知识库：包含证型分类、核心症状、鉴别要点、追问问题、调理建议、禁忌、红旗症状和审核状态。
- 本地检索召回：使用字符 n-gram TF-IDF + 关键词重合度做混合检索，支持自然语言症状描述召回候选证型。
- Embedding 向量检索：提供可插拔向量检索模块，并使用离线 hashing embedding 完成本地检索与复现实验。
- 结构化问诊槽位：从自然语言中抽取寒热、出汗、口渴、二便、睡眠、情绪、疼痛部位、持续时间和严重程度，并在问诊状态中增量合并。
- 安全 RAG 回答生成：基于检索记录、来源字段和结构化槽位生成候选方向、证据、追问、来源和安全边界；红旗症状时停止普通回答。
- 多轮问诊状态管理：根据候选证型动态选择追问问题，并把多轮回答合并后重新排序。
- 安全分流机制：识别胸痛、呼吸困难、呕血、黑便、意识异常、持续高热等红旗症状，并支持简单否定词识别。
- Web 演示和评估：提供 Streamlit 页面和基础评估脚本，便于展示项目效果。
- 产品化展示：提供检索模式切换、结构化槽位面板、来源/审核状态展示、架构图和运行手册。

## 目录结构

```text
中医问诊辅助RAG系统/
├── app/                    # Streamlit Web 演示
├── data/                   # 知识库、评估集与向量索引
├── docs/                   # 项目文档（架构、来源、运行手册、多模型说明）
├── reports/                # 评估报告（可复跑生成）
├── src/tcm_agent/          # 核心 Python 包
├── tests/                  # 评估与校验脚本
└── tools/                  # 知识库维护脚本
```

> C/C++ 终端版（立项阶段作品）位于仓库根目录的 `../terminal/`。

## 快速运行

Windows 首次使用推荐直接双击：

- `启动_网页演示.bat`

脚本会检查 Python，缺失时安装官方 Python 3.12，然后创建 `.venv`、安装依赖并启动 Streamlit。首次需要联网。

如需在命令行中准备环境：

```bash
powershell -ExecutionPolicy Bypass -File .\环境准备.ps1
```

运行命令行演示：

```bash
python -m tcm_agent.cli --demo
```

运行 embedding 检索演示：

```bash
python -m tcm_agent.cli --demo --retrieval embedding
```

### 换电脑运行（可移植说明）

1. 目标电脑安装 Python 3.10+（安装时勾选 “Add Python to PATH”）；
2. 双击 `启动_网页演示.bat`，脚本会自动完成 Python、`.venv` 和 Streamlit 依赖准备；
3. 命令行演示双击 `启动_命令行演示.bat`；
4. 需要大模型时：把密钥填进项目根目录的 `.env` 文件（模板已备好），重启程序生效。

运行基础评估：

```bash
python tests/evaluate_agent.py
```

运行 embedding 检索评估：

```bash
python tests/evaluate_embedding_retrieval.py
```

运行结构化槽位评估：

```bash
python tests/evaluate_structured_slots.py
```

运行 RAG 回答生成评估：

```bash
python tests/evaluate_rag_generation.py
```

启动脚本会自动检查并补齐环境，也可以直接运行 Web 页面：

```bash
streamlit run app/streamlit_app.py
```

本地访问：`http://localhost:8501`

## 当前评估结果

当前基础评估集包含 6 条用例：

- Top1 候选命中：6/6
- 红旗症状识别：6/6
- Embedding Top3 候选命中：6/6
- 结构化槽位评测：4/4
- RAG 来源/安全边界评测：通过
- 综合评估集：20 条用例；明确目标检索 Top1/Top3 均为 16/16，红旗 Precision/Recall 为 1.000/1.000，低置信度识别 2/2。
- 2026-10 复测报告：`reports/evaluation_report_v3.json`（综合评估保持 16/16、1.000/1.000、2/2、12/12、5/5）。

评估覆盖：食积停滞、痰湿咳嗽、风热感冒、风寒感冒、红旗症状分流、否定表达处理。

