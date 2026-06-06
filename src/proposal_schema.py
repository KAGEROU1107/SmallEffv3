"""
SmallEFFV3 Part 2 — Proposal Schema

Defines the structured proposal contract for governed Casper transactions.
All proposals must pass schema validation before policy evaluation.
"""

from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime, timezone
from typing import Any

PROPOSAL_VERSION = "1.0"
ALLOWED_ACTIONS = {"TRANSFER_CSPR"}
ALLOWED_NETWORKS = {"casper-test"}
MAX_REASON_LENGTH = 512
CASPER_ACCOUNT_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
CASPER_ACCOUNT_PEM_PATTERN = re.compile(r"^-----BEGIN PUBLIC KEY-----")


def canonical_json(data: dict[str, Any]) -> str:
    """Deterministic JSON serialization — sorted keys, compact, ASCII-safe."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_recipient(recipient: str) -> list[str]:
    """Validate Casper account identifier format."""
    errors = []
    if not recipient or not recipient.strip():
        errors.append("RECIPIENT_EMPTY")
        return errors
    recipient = recipient.strip()
    if not CASPER_ACCOUNT_HEX_PATTERN.match(recipient):
        errors.append("RECIPIENT_INVALID")
    return errors


def validate_amount(amount_motes: Any) -> list[str]:
    """Validate amount — must be a positive integer."""
    errors = []
    if amount_motes is None:
        errors.append("AMOUNT_MISSING")
        return errors
    if isinstance(amount_motes, bool):
        errors.append("AMOUNT_INVALID")
        return errors
    if isinstance(amount_motes, float):
        errors.append("AMOUNT_INVALID")
        return errors
    if isinstance(amount_motes, str):
        try:
            amount_motes = int(amount_motes)
        except (ValueError, TypeError):
            errors.append("AMOUNT_INVALID")
            return errors
    if not isinstance(amount_motes, int):
        errors.append("AMOUNT_INVALID")
        return errors
    if amount_motes <= 0:
        errors.append("AMOUNT_INVALID")
        return errors
    if amount_motes > 10_000_000_000_000:
        errors.append("AMOUNT_TOO_LARGE")
    return errors


def build_proposal(
    action: str,
    recipient: str,
    amount_motes: int,
    reason: str,
    network: str = "casper-test",
) -> dict[str, Any]:
    """
    Build a validated, hash-bound proposal.

    Required fields:
        action:      TRANSFER_CSPR
        recipient:   64-char hex Casper account identifier
        amount_motes: positive integer (1 mote = 1e-9 CSPR)
        reason:      human-readable justification (max 512 chars)
        network:     casper-test

    Returns:
        dict with proposal_id, all fields, proposal_hash
    """
    errors = []

    # Action
    if action not in ALLOWED_ACTIONS:
        errors.append(("ACTION_NOT_ALLOWED", action))

    # Network
    if network not in ALLOWED_NETWORKS:
        errors.append(("NETWORK_NOT_ALLOWED", network))

    # Recipient
    recipient_errors = validate_recipient(recipient)
    errors.extend([("RECIPIENT_INVALID", recipient)] if recipient_errors else [])

    # Amount
    amount_errors = validate_amount(amount_motes)
    errors.extend([("AMOUNT_INVALID")] if amount_errors else [])

    # Reason
    if not reason or not reason.strip():
        errors.append(("REASON_EMPTY", ""))
    elif len(reason) > MAX_REASON_LENGTH:
        errors.append(("REASON_TOO_LONG", f"{len(reason)} > {MAX_REASON_LENGTH}"))

    if errors:
        return {
            "valid": False,
            "errors": [e[0] if isinstance(e, tuple) else e for e in errors],
        }

    amount_motes = int(amount_motes)

    proposal = {
        "proposal_version": PROPOSAL_VERSION,
        "proposal_id": f"prop-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{hashlib.sha256(recipient.encode()).hexdigest()[:8]}",
        "action": action,
        "recipient": recipient.strip(),
        "amount_motes": str(amount_motes),
        "network": network,
        "reason": reason.strip(),
        "created_at": utc_now_rfc3339(),
        "proposal_hash": "",
    }

    # Hash over canonical JSON excluding the hash field itself
    hash_body = {k: v for k, v in proposal.items() if k != "proposal_hash"}
    proposal["proposal_hash"] = sha256_hex(canonical_json(hash_body))

    return {
        "valid": True,
        "proposal": proposal,
    }


def verify_proposal_hash(proposal: dict[str, Any]) -> bool:
    """Verify that a proposal's hash matches its content."""
    stored_hash = proposal.get("proposal_hash", "")
    hash_body = {k: v for k, v in proposal.items() if k != "proposal_hash"}
    computed = sha256_hex(canonical_json(hash_body))
    return stored_hash == computed


def proposal_to_cspr_amount(amount_motes: int) -> float:
    """Convert motes to CSPR (1 CSPR = 1e9 motes)."""
    return amount_motes / 1_000_000_000.0
