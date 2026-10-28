from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.error
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent import GroundedRAGGenerator, load_records
from tcm_agent.config import DEFAULT_SOURCED_KB_PATH
from tcm_agent.llm_slots import extract_slots_with_llm
from tcm_agent.llm_generation import DeepSeekGenerator
from tcm_agent.llm_providers import PROVIDER_PRESETS, list_providers, make_generator
from tcm_agent.models import Record

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SAFE_TEXT = (
    "候选方向：心气虚证可能相关。"
    "依据：检索记录中的心悸、失眠多梦等表现。"
    "来源：见检索上下文中的来源字段。"
    "建议追问：睡眠质量、活动后是否气短。"
    "安全提醒：如出现胸痛或呼吸困难，请及时线下就医。"
)


def fake_transport(content: str):
    def _transport(url, payload, headers, timeout):
        return json.dumps(
            {"choices": [{"message": {"content": content}}]},
            ensure_ascii=False,
        )

    return _transport


def failing_transport(url, payload, headers, timeout):
    raise TimeoutError("simulated timeout")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="大模型生成与安全回退评估")
    parser.add_argument("--live", action="store_true", help="使用真实 DEEPSEEK_API_KEY 调用一次")
    args = parser.parse_args(argv)

    errors: list[str] = []
    records = load_records(DEFAULT_SOURCED_KB_PATH)
    record = records[0]
    matches = [(record, 0.8)]
    generator = GroundedRAGGenerator()

    print("========== 大模型生成与安全回退评估 ==========")
    print(f"测试记录：{record.name}")
    print("")

    no_key = DeepSeekGenerator(api_key="")
    if no_key.available:
        errors.append("空 Key 时 available 应为 False")
    fallback = generator.render_with_llm(
        "心悸，失眠多梦",
        {"睡眠": ["多梦"]},
        matches,
        llm=no_key,
    )
    if fallback.used_llm:
        errors.append("无 Key 时不应使用大模型")
    print(f"无 Key 回退：{fallback.note}")

    calls = {"count": 0}

    def counting_transport(url, payload, headers, timeout):
        calls["count"] += 1
        return fake_transport(SAFE_TEXT)(url, payload, headers, timeout)

    safe = DeepSeekGenerator(api_key="test", transport=counting_transport)
    safe_result = generator.render_with_llm(
        "心悸，失眠多梦",
        {"睡眠": ["多梦"]},
        matches,
        llm=safe,
    )
    if not safe_result.used_llm:
        errors.append(f"安全输出应使用大模型：{safe_result.note}")
    if calls["count"] != 1:
        errors.append(f"安全输出应恰好调用一次，实际 {calls['count']}")
    print(f"安全输出：used_llm={safe_result.used_llm} | {safe_result.note}")

    unsafe = DeepSeekGenerator(
        api_key="test",
        transport=fake_transport("确诊为心气虚证，必须服用归脾汤。"),
    )
    unsafe_result = generator.render_with_llm(
        "心悸，失眠多梦",
        {"睡眠": ["多梦"]},
        matches,
        llm=unsafe,
    )
    if unsafe_result.used_llm or "安全过滤" not in unsafe_result.note:
        errors.append(f"违规输出应被拦截：{unsafe_result.note}")
    print(f"违规输出：used_llm={unsafe_result.used_llm} | {unsafe_result.note}")

    broken = DeepSeekGenerator(api_key="test", transport=failing_transport)
    broken_result = generator.render_with_llm(
        "心悸，失眠多梦",
        {"睡眠": ["多梦"]},
        matches,
        llm=broken,
    )
    if broken_result.used_llm or "回退" not in broken_result.note:
        errors.append(f"网络失败应回退：{broken_result.note}")
    print(f"网络失败：used_llm={broken_result.used_llm} | {broken_result.note}")

    red_calls = {"count": 0}

    def red_transport(url, payload, headers, timeout):
        red_calls["count"] += 1
        return fake_transport(SAFE_TEXT)(url, payload, headers, timeout)

    red = DeepSeekGenerator(api_key="test", transport=red_transport)
    red_result = generator.render_with_llm(
        "胸痛，呼吸困难",
        {},
        matches,
        llm=red,
    )
    if red_result.used_llm or "安全分流" not in red_result.text:
        errors.append("红旗症状应优先安全分流")
    if red_calls["count"] != 0:
        errors.append("红旗症状不应调用大模型")
    print(f"红旗分流：used_llm={red_result.used_llm} | 调用次数={red_calls['count']}")

    citation = DeepSeekGenerator(
        api_key="test",
        transport=fake_transport(
            "候选方向：心阳虚证可能相关。依据：见检索上下文。来源：见上下文。"
            "建议追问：睡眠质量。安全提醒：如出现胸痛请及时就医。"
        ),
    )
    citation_result = generator.render_with_llm(
        "心悸，失眠多梦",
        {"睡眠": ["多梦"]},
        matches,
        llm=citation,
        known_names=[record.name, "心阳虚证"],
    )
    if citation_result.used_llm or "检索上下文之外" not in citation_result.note:
        errors.append(f"引用越界应回退：{citation_result.note}")
    print(f"引用校验：used_llm={citation_result.used_llm} | {citation_result.note}")

    retry_sequence = {"count": 0}

    def citation_retry_transport(url, payload, headers, timeout):
        retry_sequence["count"] += 1
        if retry_sequence["count"] == 1:
            return fake_transport(
                "候选方向：心阳虚证可能相关。依据：见检索上下文。来源：见上下文。"
                "建议追问：睡眠质量。安全提醒：如出现胸痛请及时就医。"
            )(url, payload, headers, timeout)
        return fake_transport(SAFE_TEXT)(url, payload, headers, timeout)

    retry_llm = DeepSeekGenerator(api_key="test", transport=citation_retry_transport)
    retry_result = generator.render_with_llm(
        "心悸，失眠多梦",
        {"睡眠": ["多梦"]},
        matches,
        llm=retry_llm,
        known_names=[record.name, "心阳虚证"],
    )
    if not retry_result.used_llm or "重试" not in retry_result.note:
        errors.append(f"引用校验重试应通过：used_llm={retry_result.used_llm}, note={retry_result.note}")
    if retry_sequence["count"] != 2:
        errors.append(f"引用校验重试应调用两次：实际 {retry_sequence['count']}")
    print(f"引用重试：used_llm={retry_result.used_llm} | 调用次数={retry_sequence['count']} | {retry_result.note}")

    flaky_calls = {"count": 0}

    def flaky_transport(url, payload, headers, timeout):
        flaky_calls["count"] += 1
        if flaky_calls["count"] == 1:
            raise TimeoutError("simulated transient timeout")
        return fake_transport(SAFE_TEXT)(url, payload, headers, timeout)

    flaky = DeepSeekGenerator(api_key="test", transport=flaky_transport, max_retries=1)
    flaky_result = flaky.generate("测试提示词")
    if not flaky_result.ok or flaky_result.attempts != 2:
        errors.append(f"瞬时失败应重试一次：ok={flaky_result.ok}, attempts={flaky_result.attempts}")
    print(f"重试机制：ok={flaky_result.ok} | 尝试次数={flaky_result.attempts}")

    temp_calls = {"temperatures": []}

    def temperature_transport(url, payload, headers, timeout):
        temp_calls["temperatures"].append(payload.get("temperature"))
        if payload.get("temperature") != 1:
            raise urllib.error.HTTPError(
                url,
                400,
                "Bad Request",
                None,
                io.BytesIO(
                    b'{"error":{"message":"invalid temperature: only 1 is allowed for this model"}}'
                ),
            )
        return fake_transport(SAFE_TEXT)(url, payload, headers, timeout)

    temp_llm = DeepSeekGenerator(api_key="test", transport=temperature_transport, temperature=0.2)
    temp_result = temp_llm.generate("测试提示词")
    if not temp_result.ok or temp_calls["temperatures"] != [0.2, 1]:
        errors.append(f"温度自适应失败：ok={temp_result.ok}, calls={temp_calls['temperatures']}")
    print(f"温度自适应：ok={temp_result.ok} | 参数序列={temp_calls['temperatures']}")

    synthetic = Record(
        id="T900",
        name="心气虚证",
        category="虚证",
        core_symptoms="心悸；气短",
        differentiation_points="气虚表现并见",
        care_advice="注意休息，避免劳累",
        diet_advice="饮食清淡",
        lifestyle_advice="规律作息",
        prescription_reference="归脾汤",
        review_status="待中医专业审核",
        source_title="《中医诊断学》",
        source_url="https://example.com",
        source_locator="心与小肠病辨证",
    )
    report = generator.render("心悸，气短", {}, [(synthetic, 0.8)])
    for required in ["调理方向参考", "传统知识参考", "归脾汤", "不可自行服用", "安全提醒", "来源状态："]:
        if required not in report:
            errors.append(f"结构化报告缺少：{required}")
    for banned in ["必须服用", "剂量"]:
        if banned in report:
            errors.append(f"结构化报告不应出现：{banned}")
    print("结构化报告：包含调理/方剂参考与免责声明，无违禁词")

    slot_llm = DeepSeekGenerator(
        api_key="test",
        transport=fake_transport('{"寒热": ["发热", "怕冷"], "出汗": ["无汗"], "不存在的槽位": ["x"]}'),
    )
    slots_ok, slot_err = extract_slots_with_llm(slot_llm, "发烧怕冷，没有汗")
    if slots_ok != {"寒热": ["发热", "怕冷"], "出汗": ["无汗"]}:
        errors.append(f"大模型槽位抽取结果不符：{slots_ok} ({slot_err})")
    bad_llm = DeepSeekGenerator(api_key="test", transport=fake_transport("我不知道"))
    slots_bad, bad_err = extract_slots_with_llm(bad_llm, "随便说点什么")
    if slots_bad or not bad_err:
        errors.append("非法 JSON 应返回空结果和错误说明")
    print(f"大模型槽位抽取：正常={slots_ok} | 异常回退说明={bad_err!r}")

    for key, preset in PROVIDER_PRESETS.items():
        provider_gen = make_generator(key, max_tokens=32)
        if provider_gen.endpoint != preset["base_url"] or provider_gen.model != preset["default_model"]:
            errors.append(f"厂商预设不正确：{key} => {provider_gen.endpoint} / {provider_gen.model}")
    print(f"厂商预设：{list_providers()} 的端点与默认模型均正确")

    if args.live:
        live = DeepSeekGenerator(max_tokens=256)
        if not live.available:
            errors.append("--live 需要 DEEPSEEK_API_KEY")
        else:
            prompt = generator.build_prompt("心悸，失眠多梦", {"睡眠": ["多梦"]}, matches)
            live_result = live.generate(prompt)
            if not live_result.ok:
                errors.append(f"真实调用失败：{live_result.error}")
            else:
                violation = generator.check_safety(live_result.text)
                if violation:
                    errors.append(f"真实输出触发安全过滤：{violation}")
                preview = " ".join(live_result.text.split())[:160]
                print(f"真实调用成功（{live_result.model}）：{preview}...")

    if errors:
        print("")
        print("发现问题：")
        for error in errors:
            print("- " + error)
        return 1

    print("")
    print("评估通过：大模型可选接入、安全过滤与离线回退均正常。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
