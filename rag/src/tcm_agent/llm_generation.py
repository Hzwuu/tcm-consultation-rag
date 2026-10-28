from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


DEFAULT_ENDPOINT = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

# HTTP 状态码中属于"可重试"的瞬时错误
TRANSIENT_HTTP_CODES = {429, 500, 502, 503, 504}

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def load_env_file(path: Path | None = None) -> None:
    """Load KEY=VALUE pairs from the project's `.env` file.

    Machine-level environment variables always keep priority: a variable is
    only set when it is not already present in the environment.
    """
    target = Path(path) if path else ENV_FILE
    try:
        content = target.read_text(encoding="utf-8-sig")
    except OSError:
        return
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


load_env_file()

PROVIDER_KEY_ENV = (
    ("moonshot.cn", "KIMI_API_KEY"),
    ("deepseek.com", "DEEPSEEK_API_KEY"),
    ("dashscope.aliyuncs.com", "DASHSCOPE_API_KEY"),
)


def resolve_api_key(endpoint: str) -> str:
    """Resolve the API key from environment variables.

    Priority: TCM_LLM_API_KEY, then the vendor variable matching the endpoint
    domain (deepseek / kimi / dashscope), then DEEPSEEK_API_KEY as default.
    """
    generic = os.getenv("TCM_LLM_API_KEY", "")
    if generic:
        return generic
    for domain, env_name in PROVIDER_KEY_ENV:
        if domain in endpoint:
            provider_key = os.getenv(env_name, "")
            if provider_key:
                return provider_key
    return os.getenv("DEEPSEEK_API_KEY", "")


SYSTEM_PROMPT = (
    "你是中医健康咨询辅助系统的回答生成器。"
    "只能使用用户消息中提供的检索上下文，不得补充上下文之外的医学事实。"
    "不得输出确诊结论、必须服用某方、用法用量或自行购药建议。"
    "方剂只能作为“传统知识参考”列出名称，并注明不可自行服用。"
    "方剂名称只能来自检索上下文；检索上下文未提供方剂时，必须说明未提供，不得自行补充其他方剂。"
    "只能提及检索上下文中的证型名称，不得自行推断其他证型。"
    "如果检测到红旗症状，只输出及时线下就医的安全分流。"
    "如果最高检索相关度低于可信阈值，不要强行选择候选证型。"
    "请用简洁中文按“候选方向、依据、来源、建议追问、调理方向参考、传统知识参考、安全提醒”输出。"
)


@dataclass(frozen=True)
class LLMResult:
    ok: bool
    text: str = ""
    error: str = ""
    model: str = ""
    attempts: int = 1


Transport = Callable[[str, dict, dict, float], str]


def _default_transport(url: str, payload: dict, headers: dict, timeout: float) -> str:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


class DeepSeekGenerator:
    """Optional DeepSeek adapter.

    The API key is read from the DEEPSEEK_API_KEY environment variable and is
    never written into project files. When the key is missing, the network is
    unavailable, or the response fails validation, callers fall back to the
    local deterministic generator.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        endpoint: str | None = None,
        timeout: float = 60.0,
        max_tokens: int = 700,
        temperature: float = 0.2,
        transport: Transport | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.endpoint = endpoint or os.getenv("TCM_LLM_BASE_URL", DEFAULT_ENDPOINT)
        self.api_key = api_key if api_key is not None else resolve_api_key(self.endpoint)
        self.model = model or os.getenv("TCM_LLM_MODEL", DEFAULT_MODEL)
        env_timeout = os.getenv("TCM_LLM_TIMEOUT", "")
        if env_timeout:
            try:
                timeout = float(env_timeout)
            except ValueError:
                pass
        env_temperature = os.getenv("TCM_LLM_TEMPERATURE", "")
        if env_temperature:
            try:
                temperature = float(env_temperature)
            except ValueError:
                pass
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.transport = transport or _default_transport
        if max_retries is None:
            try:
                max_retries = int(os.getenv("TCM_LLM_MAX_RETRIES", "1"))
            except ValueError:
                max_retries = 1
        self.max_retries = max(0, max_retries)

    @property
    def available(self) -> bool:
        return bool(self.api_key.strip())

    def status_text(self) -> str:
        if self.available:
            return f"已配置（{self.model}）"
        return "未配置 DEEPSEEK_API_KEY"

    def generate(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> LLMResult:
        if not self.available:
            return LLMResult(False, error="未配置 DEEPSEEK_API_KEY")
        if not prompt.strip():
            return LLMResult(False, error="提示词为空")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        attempts = 0
        last_error = "调用失败"
        temperature_adapted = False
        while attempts <= self.max_retries:
            attempts += 1
            try:
                raw = self.transport(self.endpoint, payload, headers, self.timeout)
            except urllib.error.HTTPError as exc:
                body = ""
                try:
                    body = exc.read().decode("utf-8", "ignore")
                except Exception:  # noqa: BLE001
                    body = ""
                last_error = f"HTTP {exc.code}"
                if (
                    exc.code == 400
                    and "temperature" in body.lower()
                    and not temperature_adapted
                ):
                    # 部分国产推理模型（如 Kimi k 系列）只接受 temperature=1。
                    temperature_adapted = True
                    payload["temperature"] = 1
                    last_error = "HTTP 400：temperature 参数不兼容，已自动适配为 1 重试"
                    continue
                if exc.code in TRANSIENT_HTTP_CODES and attempts <= self.max_retries:
                    time.sleep(min(3.0, 1.0 * attempts))
                    continue
                break
            except urllib.error.URLError as exc:
                last_error = f"网络错误：{exc.reason}"
                if attempts <= self.max_retries:
                    time.sleep(min(3.0, 1.0 * attempts))
                    continue
                break
            except TimeoutError:
                last_error = "请求超时"
                if attempts <= self.max_retries:
                    time.sleep(min(3.0, 1.0 * attempts))
                    continue
                break
            except Exception as exc:  # noqa: BLE001 - never leak key material
                last_error = str(exc)[:120]
                break

            try:
                data = json.loads(raw)
            except Exception:  # noqa: BLE001
                return LLMResult(False, error="响应不是有效 JSON", model=self.model, attempts=attempts)

            choices = data.get("choices") or []
            if not choices:
                return LLMResult(False, error="响应中没有 choices", model=self.model, attempts=attempts)
            message = choices[0].get("message") or {}
            text = (message.get("content") or "").strip()
            if not text:
                # 推理型模型可能把内容放在 reasoning_content 字段。
                text = (message.get("reasoning_content") or "").strip()
            if not text:
                return LLMResult(False, error="模型返回空内容", model=self.model, attempts=attempts)
            return LLMResult(True, text=text, model=self.model, attempts=attempts)

        return LLMResult(False, error=last_error, model=self.model, attempts=attempts)
