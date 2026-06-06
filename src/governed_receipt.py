"""
SmallEFFV3 Part 2 — Governed Receipt Generator

Generates hash-bound receipts for the full governance lineage:
proposal + policy + human confirmation + Casper transaction.
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from typing import Any

from src.proposal_schema import canonical_json, sha256_hex

RECEIPT_VERSION = "1.0"


def build_receipt(
    proposal: dict[str, Any],
    policy_result: dict[str, Any],
    human_confirmation: dict[str, Any],
    casper_network: str = "casper-test",
    contract_hash: str = "",
    entry_point: str = "record_proposal",
    transaction_hash: str = "",
    transaction_status: str = "",
) -> dict[str, Any]:
    """
    Build a hash-bound governed receipt.

    The receipt captures the full lineage:
    - What was proposed (proposal_hash)
    - What the policy decided (policy_hash)
    - What the human confirmed (confirmation_hash)
    - What was submitted on-chain (transaction_hash)
    """
    submitted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Hash the human confirmation
    confirmation_hash = sha256_hex(canonical_json(human_confirmation)) if human_confirmation else ""

    receipt = {
        "receipt_version": RECEIPT_VERSION,
        "proposal_hash": proposal.get("proposal_hash", ""),
        "policy_hash": policy_result.get("policy_hash", ""),
        "human_confirmation_hash": confirmation_hash,
        "casper_network": casper_network,
        "contract_hash": contract_hash,
        "entry_point": entry_point,
        "transaction_hash": transaction_hash,
        "submitted_at": submitted_at,
        "confirmed_at": human_confirmation.get("confirmed_at", ""),
        "transaction_status": transaction_status,
        "receipt_hash": "",
    }

    # Hash over canonical JSON excluding the hash field
    hash_body = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    receipt["receipt_hash"] = sha256_hex(canonical_json(hash_body))

    return receipt


def verify_receipt_hash(receipt: dict[str, Any]) -> bool:
    """Verify that a receipt's hash matches its content."""
    stored_hash = receipt.get("receipt_hash", "")
    hash_body = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    computed = sha256_hex(canonical_json(hash_body))
    return stored_hash == computed


def save_receipt(receipt: dict[str, Any], directory: str | None = None) -> Path:
    """Save receipt to runtime/receipts/ (gitignored)."""
    from pathlib import Path
    if directory is None:
        directory = "runtime/receipts"
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)

    receipt_id = f"receipt-{receipt['proposal_hash'][:16]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    file_path = dir_path / f"{receipt_id}.json"
    file_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return file_path


def sanitize_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    """Return a copy safe for public sharing (no sensitive fields)."""
    safe_fields = [
        "receipt_version", "proposal_hash", "policy_hash",
        "human_confirmation_hash", "casper_network", "contract_hash",
        "entry_point", "transaction_hash", "submitted_at", "confirmed_at",
        "transaction_status", "receipt_hash",
    ]
    return {k: v for k, v in receipt.items() if k in safe_fields}
