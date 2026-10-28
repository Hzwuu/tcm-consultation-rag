# TCM Consultation Agent

一个面向中医健康咨询场景的学习与竞赛原型。项目包含 C/C++ 终端版和 Python 本地 RAG 版，用于演示结构化知识检索、来源展示、多轮问诊、安全分流和本地回退。

> 本项目不提供医学诊断或处方，不能替代医生。方剂名称只作为传统知识参考，不可自行服用。

## 项目内容

- `terminal/`：V1.0 与 V1.2 C/C++ 终端程序源码和 CSV 病症数据。
- `rag/`：Python 本地 RAG、命令行、Streamlit 网页、知识库和测试。
- 基础知识库：15 条常见病症记录。
- 来源版知识库：20 条带来源和审核字段的证型记录。
- 来源索引：58 条证名与来源覆盖数据，不参与默认问诊检索。
- 检索模式：TF-IDF 和本地哈希 Embedding。
- 可选生成模型：DeepSeek、Kimi、通义千问的 OpenAI 兼容接口。
- 安全机制：红旗症状优先分流、低置信度停止、模型输出过滤和本地模板回退。
- 记录完整性：本地 SHA-256 哈希链原型，不是区块链。

## RAG 流程

```text
用户输入
→ 同义词、错别字和否定表达处理
→ 从当前 CSV 知识库检索 Top 3
→ 将候选、依据、来源和追问问题装入上下文
→ 可选大模型生成或本地模板生成
→ 安全检查与失败回退
```

大模型不负责知识检索、候选排序或红旗判断。

## 快速运行

### Python RAG 网页

```powershell
Set-Location .\rag
powershell -ExecutionPolicy Bypass -File .\环境准备.ps1
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

浏览器访问 `http://localhost:8501`。

### Python 命令行

```powershell
Set-Location .\rag
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m tcm_agent.cli --demo
.\.venv\Scripts\python.exe -m tcm_agent.cli --demo --kb-mode sourced
```

启用大模型前，复制 `rag/.env.example` 为 `rag/.env`，填写自己的密钥。不要提交 `.env`。

### C/C++ 终端

```powershell
Set-Location .\terminal
g++ -std=c++17 -O2 -finput-charset=UTF-8 -fexec-charset=UTF-8 "中医问诊智能体_V1.2_当前版_源码.cpp" -o "中医问诊智能体_V1.2_当前版.exe"
.\中医问诊智能体_V1.2_当前版.exe
```

终端程序必须和 `tcm_data.csv` 位于同一目录。

## 测试

```powershell
Set-Location .\rag
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe tests\evaluate_system.py
.\.venv\Scripts\python.exe tests\evaluate_accuracy.py
.\.venv\Scripts\python.exe tests\evaluate_ledger.py
```

测试结果来自自建工程测试集，不代表临床有效性或真实用户准确率。

## 数据与限制

- 知识库规模较小，来源版记录大多仍待中医专业审核。
- 默认 Embedding 是依赖无模型的哈希向量，不是 BGE 等神经语义模型。
- 没有使用外部向量数据库或神经重排序模型。
- 没有实现自动联网检索或来源内容实时核验。
- 项目定位为学习、竞赛和健康咨询辅助原型。

## 开发说明

项目开发使用了生成式 AI 辅助代码和文档实现。提交者负责需求确定、方案取舍、数据边界、运行验收和版本整合。仓库中的测试与已知局限用于说明项目当前能够验证和不能验证的范围。

