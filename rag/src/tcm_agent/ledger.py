from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


GENESIS_HASH = "0" * 64


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def block_hash(index: int, timestamp: str, digest: str, previous_hash: str) -> str:
    text = f"{index}|{timestamp}|{digest}|{previous_hash}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class HashChainLedger:
    """Local SHA-256 hash-chain prototype.

    This is NOT Hyperledger Fabric, NOT a distributed ledger, and has no
    consensus or smart contracts. It only demonstrates tamper-evident local
    record keeping: every block links to the previous block's hash, and any
    modification breaks verification.
    """

    path: Path
    blocks: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self.blocks = list(payload.get("blocks", []))

    @property
    def last_hash(self) -> str:
        return self.blocks[-1]["block_hash"] if self.blocks else GENESIS_HASH

    def append(self, payload: dict, label: str = "问诊小结") -> dict:
        record = {
            "index": len(self.blocks),
            "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "label": label,
            "payload_hash": payload_hash(payload),
            "previous_hash": self.last_hash,
        }
        record["block_hash"] = block_hash(
            record["index"],
            record["timestamp"],
            record["payload_hash"],
            record["previous_hash"],
        )
        self.blocks.append(record)
        self.save()
        return record

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"blocks": self.blocks}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def verify(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        previous = GENESIS_HASH
        for position, block in enumerate(self.blocks):
            if block.get("index") != position:
                errors.append(f"块 {position} 的 index 不连续")
            if block.get("previous_hash") != previous:
                errors.append(f"块 {position} 的 previous_hash 与上一块不匹配")
            expected = block_hash(
                int(block.get("index", -1)),
                str(block.get("timestamp", "")),
                str(block.get("payload_hash", "")),
                str(block.get("previous_hash", "")),
            )
            if block.get("block_hash") != expected:
                errors.append(f"块 {position} 的 block_hash 不匹配，可能被篡改")
            previous = str(block.get("block_hash", ""))
        return (not errors), errors

    @staticmethod
    def verify_payload(block: dict, payload: dict) -> bool:
        return block.get("payload_hash") == payload_hash(payload)
