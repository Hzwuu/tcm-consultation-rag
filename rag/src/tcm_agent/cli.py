from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import DEFAULT_KB_PATH, DEFAULT_SOURCED_KB_PATH
from .consultation import TCMConsultAgent
from .knowledge_base import load_records
from .ledger import HashChainLedger
from .llm_generation import DeepSeekGenerator
from .llm_providers import PROVIDER_PRESETS
from .safety import detect_red_flags


def configure_console() -> None:
    if sys.platform.startswith("win"):
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleCP(65001)
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass

    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def write_report(path: str, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"\n报告已保存：{target}")


def run_demo(
    agent: TCMConsultAgent,
    llm=None,
    suite: str = "basic",
    ledger=None,
    use_llm_slots: bool = False,
    report_out: str | None = None,
) -> None:
    if suite == "sourced":
        answers = [
            "心悸，胸闷，活动后气短，容易出汗",
            "没有胸痛，也没有呼吸困难",
            "最近胃口一般，睡眠还可以",
        ]
    else:
        answers = [
            "最近胃胀，打嗝有酸腐味，不想吃饭",
            "昨天晚上吃太多烧烤以后开始的",
            "有点腹胀恶心，没有剧烈腹痛",
            "大便有点酸臭，小便正常",
        ]

    print("========== 自动演示：普通问诊流程 ==========")
    state = agent.start(answers[0], llm=llm, use_llm_slots=use_llm_slots)
    print(f"用户：{answers[0]}")
    print_current_matches(agent, state)

    for answer in answers[1:]:
        question = agent.next_question(state)
        if question is None:
            break
        print(f"\n智能体追问：{question}")
        print(f"用户：{answer}")
        state.add_answer(question, answer, llm=llm, use_llm_slots=use_llm_slots)
        print_current_matches(agent, state)

    print()
    summary = agent.summary(state, llm=llm)
    print(summary)
    if report_out:
        write_report(report_out, summary)
    if ledger is not None:
        block = ledger.append({"summary": summary, "terms": state.query_terms}, label="问诊小结")
        print(
            f"\n本地存证：已写入第 {block['index']} 块，"
            f"block_hash={block['block_hash'][:16]}...（仅本地防篡改原型）"
        )

    print("\n\n========== 自动演示：红旗症状分流 ==========")
    urgent_state = agent.start("胸痛，呼吸困难，还头晕")
    print("用户：胸痛，呼吸困难，还头晕")
    print()
    print(agent.summary(urgent_state, llm=llm))


def print_current_matches(agent: TCMConsultAgent, state) -> None:
    print("\n当前候选：")
    for index, (record, score) in enumerate(agent.current_matches(state), start=1):
        print(f"{index}. {record.name}（相关度 {score:.3f}）")


def run_interactive(
    agent: TCMConsultAgent,
    llm=None,
    ledger=None,
    use_llm_slots: bool = False,
    report_out: str | None = None,
) -> None:
    print("中医问诊辅助系统")
    print("说明：本系统仅用于学习演示，不能替代医生诊断。输入 q 可退出。")
    if llm is not None:
        print(f"大模型状态：{llm.status_text()}（失败会自动回退本地模板）")
    initial = input("\n请先描述你的主要不适：").strip()
    if not initial or initial.lower() in {"q", "quit", "exit", "退出"}:
        print("已退出。")
        return

    state = agent.start(initial, llm=llm, use_llm_slots=use_llm_slots)
    print_current_matches(agent, state)

    while True:
        if agent.should_stop(state):
            break

        question = agent.next_question(state)
        if not question:
            break

        answer = input(f"\n追问：{question}\n回答：").strip()
        if answer.lower() in {"q", "quit", "exit", "退出"}:
            break
        if not answer:
            print("回答不能为空。如果不清楚，可以输入“不清楚”。")
            continue

        state.add_answer(question, answer, llm=llm, use_llm_slots=use_llm_slots)
        if detect_red_flags(state.combined_text()):
            break
        print_current_matches(agent, state)

    print()
    summary = agent.summary(state, llm=llm)
    print(summary)
    if report_out:
        write_report(report_out, summary)
    if ledger is not None:
        block = ledger.append({"summary": summary, "terms": state.query_terms}, label="问诊小结")
        print(
            f"\n本地存证：已写入第 {block['index']} 块，"
            f"block_hash={block['block_hash'][:16]}...（仅本地防篡改原型）"
        )


def main(argv: list[str] | None = None) -> int:
    configure_console()
    parser = argparse.ArgumentParser(description="中医问诊辅助系统")
    parser.add_argument("--kb", default=None, help="知识库 CSV 路径（默认按 --kb-mode 选择）")
    parser.add_argument(
        "--kb-mode",
        choices=["basic", "sourced"],
        default="basic",
        help="basic=15 条基础库；sourced=20 条来源支撑库",
    )
    parser.add_argument("--demo", action="store_true", help="运行自动演示")
    parser.add_argument("--max-turns", type=int, default=4, help="最多追问轮数")
    parser.add_argument(
        "--retrieval",
        choices=["tfidf", "embedding"],
        default="tfidf",
        help="检索模式：tfidf 或 embedding",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="启用大模型生成（DeepSeek/Kimi/通义等 OpenAI 兼容接口；密钥走环境变量，失败自动回退本地模板）",
    )
    parser.add_argument("--llm-max-tokens", type=int, default=700, help="大模型最大输出 token 数")
    parser.add_argument(
        "--provider",
        choices=list(PROVIDER_PRESETS),
        default=None,
        help="大模型厂商预设（deepseek/kimi/qwen），自动启用大模型生成",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="覆盖厂商默认模型名（例如 qwen-max、kimi-k3）",
    )
    parser.add_argument(
        "--llm-slots",
        action="store_true",
        help="用大模型增强结构化槽位抽取（自动启用大模型；失败回退规则抽取）",
    )
    parser.add_argument(
        "--report-out",
        default=None,
        help="把最终问诊报告保存为 Markdown 文件（例如 reports/consultation.md）",
    )
    parser.add_argument(
        "--ledger",
        default=None,
        help="本地哈希链账本 JSON 路径；提供后把小结哈希追加到链上",
    )
    parser.add_argument(
        "--verify-ledger",
        default=None,
        help="只校验指定账本并退出（不运行问诊）",
    )
    args = parser.parse_args(argv)

    if args.verify_ledger:
        ledger = HashChainLedger(args.verify_ledger)
        ok, errors = ledger.verify()
        print(f"账本：{ledger.path}")
        print(f"块数：{len(ledger.blocks)}")
        print(f"校验结果：{'通过' if ok else '未通过'}")
        for error in errors:
            print("- " + error)
        return 0 if ok else 1

    kb_path = Path(args.kb) if args.kb else (
        DEFAULT_SOURCED_KB_PATH if args.kb_mode == "sourced" else DEFAULT_KB_PATH
    )
    records = load_records(kb_path)
    agent = TCMConsultAgent(
        records,
        max_turns=args.max_turns,
        retrieval_mode=args.retrieval,
    )
    llm = None
    if args.llm or args.llm_slots or args.provider:
        if args.provider:
            preset = PROVIDER_PRESETS[args.provider]
            llm = DeepSeekGenerator(
                model=args.model or preset["default_model"],
                endpoint=preset["base_url"],
                max_tokens=args.llm_max_tokens,
            )
        else:
            llm = DeepSeekGenerator(
                model=args.model or None,
                max_tokens=args.llm_max_tokens,
            )
    ledger = HashChainLedger(args.ledger) if args.ledger else None

    print(f"知识库：{kb_path}")
    if llm is not None:
        print(f"大模型：{llm.status_text()}")
    if ledger is not None:
        print(f"本地存证：启用（{ledger.path}）")

    if args.demo:
        run_demo(
            agent,
            llm=llm,
            suite="sourced" if args.kb_mode == "sourced" else "basic",
            ledger=ledger,
            use_llm_slots=args.llm_slots,
            report_out=args.report_out,
        )
    else:
        run_interactive(
            agent,
            llm=llm,
            ledger=ledger,
            use_llm_slots=args.llm_slots,
            report_out=args.report_out,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
