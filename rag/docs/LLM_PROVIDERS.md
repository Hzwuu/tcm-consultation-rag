# 多模型适配说明（2026-10 实测）

系统通过 OpenAI 兼容接口调用大模型，默认 DeepSeek，可切换其他国产厂商。

## 密钥填写方式（.env 文件）

- 项目根目录提供 `.env` 模板：把密钥粘贴在 `DASHSCOPE_API_KEY=` 等号后面即可；
- 优先级：**系统环境变量 > .env**（已配置系统变量的机器不受影响）；
- 修改 `.env` 后需重启命令行/网页程序才会生效；
- `.env` 只保留在本地，不要复制进提交材料或发给别人的拷贝。

## 在系统里切换（推荐）

- **网页端**：左侧「大模型（可插拔）」→ 选择厂商 → 选择模型（点「从厂商获取可用模型」可拉取你账号下的完整模型列表）→ 勾选「启用大模型生成」；
- **命令行**：

  ```powershell
  python -m tcm_agent.cli --demo --provider qwen --model qwen-plus
  python -m tcm_agent.cli --demo --provider kimi --model kimi-k3
  python -m tcm_agent.cli --demo --provider deepseek
  ```

- 未配置密钥的厂商会自动回退本地模板，不影响演示。

## 配置方式（环境变量）

| 变量 | 作用 | 默认值 |
| --- | --- | --- |
| `TCM_LLM_BASE_URL` | 接口地址 | `https://api.deepseek.com/chat/completions` |
| `TCM_LLM_MODEL` | 模型名 | `deepseek-chat` |
| `TCM_LLM_API_KEY` | 通用密钥（优先级最高） | 空 |
| `TCM_LLM_TIMEOUT` | 超时秒数 | 60 |
| `TCM_LLM_MAX_RETRIES` | 瞬时错误重试次数 | 1 |
| `TCM_LLM_TEMPERATURE` | 采样温度 | 0.2 |

密钥解析顺序：`TCM_LLM_API_KEY` → 按接口域名匹配厂商变量
（deepseek.com → `DEEPSEEK_API_KEY`；moonshot.cn → `KIMI_API_KEY`；
dashscope.aliyuncs.com → `DASHSCOPE_API_KEY`）→ `DEEPSEEK_API_KEY`。

## 厂商实测记录（2026-10-14）

| 厂商 | 状态 | 备注 |
| --- | --- | --- |
| DeepSeek | ✅ 实测通过 | 默认配置即可，多次调用成功 |
| Kimi（月之暗面） | ✅ 实测可用 | ① k 系列模型只接受 `temperature=1`，代码会自动适配重试；② 推理型模型的输出可能位于 `reasoning_content` 字段，代码已兼容；③ 存在限流（HTTP 429）与较长响应时间，超时已放宽至 60 秒并支持重试 |
| 通义千问（阿里云百炼） | ✅ 实测通过 | qwen-plus 三层验证（原生接口 / 适配器 / 完整问诊报告）；首次输出触发引用校验时自动重试后通过 |

## 切换到 Kimi 的示例

```powershell
$env:TCM_LLM_BASE_URL="https://api.moonshot.cn/v1/chat/completions"
$env:TCM_LLM_MODEL="kimi-k3"
python -m tcm_agent.cli --demo --kb-mode sourced --llm
```

（`KIMI_API_KEY` 已在环境中时无需再设置 `TCM_LLM_API_KEY`。）
