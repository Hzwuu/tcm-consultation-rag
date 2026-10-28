from __future__ import annotations

import json
import urllib.request

from .llm_generation import DeepSeekGenerator


PROVIDER_PRESETS: dict[str, dict] = {
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/chat/completions",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "kimi": {
        "label": "Kimi（月之暗面）",
        "base_url": "https://api.moonshot.cn/v1/chat/completions",
        "default_model": "kimi-k3",
        "models": ["kimi-k3", "kimi-k2.6", "kimi-k2.7-code"],
    },
    "qwen": {
        "label": "通义千问（阿里云百炼）",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "default_model": "qwen-plus",
        "models": ["qwen-plus", "qwen-turbo", "qwen-max"],
    },
}


def list_providers() -> list[str]:
    return list(PROVIDER_PRESETS)


def make_generator(provider: str, model: str | None = None, **kwargs) -> DeepSeekGenerator:
    """Build a generator for one of the preset providers (pluggable design)."""
    preset = PROVIDER_PRESETS[provider]
    return DeepSeekGenerator(
        model=model or preset["default_model"],
        endpoint=preset["base_url"],
        **kwargs,
    )


def list_provider_models(provider: str, timeout: float = 15.0) -> tuple[list[str], str]:
    """Query the provider's OpenAI-compatible /models endpoint.

    Returns (models, error). Used by the web UI's "fetch models" button.
    """
    preset = PROVIDER_PRESETS[provider]
    generator = DeepSeekGenerator(endpoint=preset["base_url"])
    if not generator.available:
        return [], "未配置该厂商密钥"
    url = preset["base_url"].replace("/chat/completions", "/models")
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {generator.api_key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [], f"获取失败：{type(exc).__name__}"
    models = [item.get("id", "") for item in data.get("data", []) if item.get("id")]
    return models, ""
