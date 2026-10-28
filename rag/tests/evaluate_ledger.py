from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent.ledger import HashChainLedger

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    print("========== 本地哈希链存证自检 ==========")
    print("说明：这是本地 SHA-256 哈希链原型，不是 Hyperledger Fabric 联盟链。")
    print("")

    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "ledger.json"
        ledger = HashChainLedger(path)

        payloads = [
            {"summary": "问诊小结一", "terms": ["胃胀"]},
            {"summary": "问诊小结二", "terms": ["失眠"]},
            {"summary": "问诊小结三", "terms": ["怕冷"]},
        ]
        blocks = [ledger.append(payload) for payload in payloads]

        ok, verify_errors = ledger.verify()
        if not ok:
            errors.append(f"正常链校验失败：{verify_errors}")
        if blocks[1]["previous_hash"] != blocks[0]["block_hash"]:
            errors.append("第 2 块未正确链接到第 1 块")
        if not HashChainLedger.verify_payload(blocks[0], payloads[0]):
            errors.append("原始 payload 校验失败")
        if HashChainLedger.verify_payload(blocks[0], {"summary": "被改过的内容"}):
            errors.append("被改过的 payload 不应通过校验")
        print(f"追加 3 条记录：链校验 {ok} | 块哈希示例 {blocks[0]['block_hash'][:16]}...")

        tampered = json.loads(path.read_text(encoding="utf-8"))
        tampered["blocks"][1]["payload_hash"] = "0" * 64
        path.write_text(json.dumps(tampered, ensure_ascii=False, indent=2), encoding="utf-8")

        tampered_ledger = HashChainLedger(path)
        tampered_ok, tampered_errors = tampered_ledger.verify()
        if tampered_ok:
            errors.append("篡改后仍然校验通过，说明链不可靠")
        if not any("不匹配" in error or "篡改" in error for error in tampered_errors):
            errors.append(f"篡改后没有给出明确错误：{tampered_errors}")
        print(f"篡改第 2 块后：链校验 {tampered_ok} | 发现错误 {tampered_errors}")

    if errors:
        print("")
        print("发现问题：")
        for error in errors:
            print("- " + error)
        return 1

    print("")
    print("自检通过：正常链可校验，篡改可被发现。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
