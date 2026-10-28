# 运行手册

## 2026-10 新增能力

```bash
# 多症状 + 同义词/错别字容错（基础 15 条库）
python -m tcm_agent.cli --demo

# 来源可追溯知识库（20 条）+ 可选 DeepSeek 生成
python -m tcm_agent.cli --demo --kb-mode sourced --llm --llm-max-tokens 256

# 结构化问诊报告：大模型生成 + 大模型槽位增强 + 导出 Markdown
python -m tcm_agent.cli --demo --kb-mode sourced --llm --llm-slots --report-out reports/consultation.md

# 新功能自检
python tests/evaluate_query_understanding.py
python tests/evaluate_negation.py
python tests/evaluate_source_backed.py
python tests/evaluate_llm_generation.py
python tests/evaluate_llm_generation.py --live

# 自建测试集准确率评测
python tests/evaluate_accuracy.py

# 本地 SHA-256 哈希链存证
python tests/evaluate_ledger.py
python -m tcm_agent.cli --demo --ledger data/local_ledger_demo.json
python -m tcm_agent.cli --verify-ledger data/local_ledger_demo.json
```

多模型切换（DeepSeek / Kimi / 通义千问）见 `docs/LLM_PROVIDERS.md`。

提交包内的统一运行入口见 `../../运行说明_提交版.md`；本文件是工程版速查。

## 大模型说明

- 密钥只从环境变量或项目 `.env` 文件读取（默认 DeepSeek，可切换 Kimi / 通义千问，见 `docs/LLM_PROVIDERS.md`），不写入其他文件。
- 没有密钥、网络失败或输出不安全时自动回退本地模板生成器。
- 红旗症状和低置信度不会调用大模型。

## 命令行演示

```bash
python -m tcm_agent.cli --demo
```

如果没有安装为包，可以临时设置路径：

```bash
$env:PYTHONPATH="src"
python -m tcm_agent.cli --demo
```

## Web 演示

```bash
streamlit run app/streamlit_app.py
```

浏览器访问 `http://localhost:8501`。运行设置默认收起，点击左上角箭头后可切换知识库、TF-IDF/Embedding、模型与存证选项。主页面显示动态来源状态、结构化线索、Top 3 候选、审核字段和安全分流。

## 基础评估

```bash
python tests/evaluate_agent.py
```

## 常见问题

### 找不到 `tcm_agent`

在项目根目录运行，并设置：

```bash
$env:PYTHONPATH="src"
```

### 没有 Streamlit

安装依赖：

```bash
pip install -r requirements.txt
```

## 运行综合评估

```bash
python tests/evaluate_system.py --report reports/evaluation_report_v3.json
```

报告输出到 `reports/evaluation_report_v3.json`；40 条自建测试集准确率报告用 `python tests/evaluate_accuracy.py` 生成。
