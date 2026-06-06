"""
SmallEFFV3 Part 2 — Deterministic Policy Engine

Evaluates proposals against deterministic rules.
No LLM involvement — pure deterministic checks.
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from typing import Any

from src.proposal_schema import (
    canonical_json,
    sha256_hex,
    ALLOWED_ACTIONS,
    ALLOWED_NETWORKS,
    MAX_REASON_LENGTH,
    validate_recipient,
    validate_amount,
    verify_proposal_hash,
)

POLICY_VERSION = "1.0"

DENIAL_CODES = {
    "ACTION_NOT_ALLOWED",
    "NETWORK_NOT_ALLOWED",
    "RECIPIENT_INVALID",
    "RECIPIENT_NOT_APPROVED",
    "AMOUNT_INVALID",
    "AMOUNT_EXCEEDS_LIMIT",
    "PROPOSAL_HASH_INVALID",
    "HUMAN_CONFIRMATION_MISSING",
    "WALLET_CONFIGURATION_MISSING",
    "CONTRACT_CONFIGURATION_MISSING",
}


def evaluate_policy(
    proposal: dict[str, Any],
    human_confirmation: dict[str, Any] | None = None,
    configuration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Deterministic policy evaluation.

    Input:
        proposal:           validated proposal dict
        human_confirmation: {proposal_hash, confirmed, confirmed_at, ...}
        configuration:      {max_test_transfer_motes, approved_recipients, ...}

    Output:
        {allow, deny_codes, evaluated_at, policy_version, policy_hash}
    """
    configuration = configuration or {}
    deny_codes: list[str] = []

    # 1. Action check
    action = proposal.get("action", "")
    if action not in ALLOWED_ACTIONS:
        deny_codes.append("ACTION_NOT_ALLOWED")

    # 2. Network check
    network = proposal.get("network", "")
    if network not in ALLOWED_NETWORKS:
        deny_codes.append("NETWORK_NOT_ALLOWED")

    # 3. Recipient format check
    recipient = proposal.get("recipient", "")
    recipient_errors = validate_recipient(recipient)
    if recipient_errors:
        deny_codes.append("RECIPIENT_INVALID")
    else:
        # Recipient allowlist check
        approved = configuration.get("approved_recipients", [])
        if approved and recipient not in approved:
            deny_codes.append("RECIPIENT_NOT_APPROVED")

    # 4. Amount check
    amount_motes = proposal.get("amount_motes", 0)
    amount_errors = validate_amount(amount_motes)
    if amount_errors:
        deny_codes.append("AMOUNT_INVALID")
    else:
        amount_motes = int(amount_motes)
        max_motes = configuration.get("max_test_transfer_motes", 10_000_000_000)
        if amount_motes > max_motes:
            deny_codes.append("AMOUNT_EXCEEDS_LIMIT")

    # 5. Proposal hash integrity
    if not verify_proposal_hash(proposal):
        deny_codes.append("PROPOSAL_HASH_INVALID")

    # 6. Human confirmation check
    if not human_confirmation or not human_confirmation.get("confirmed"):
        deny_codes.append("HUMAN_CONFIRMATION_MISSING")
    else:
        # Verify confirmation matches proposal hash
        confirmed_hash = human_confirmation.get("proposal_hash", "")
        if confirmed_hash != proposal.get("proposal_hash", ""):
            deny_codes.append("HUMAN_CONFIRMATION_MISSING")

    # 7. Wallet configuration check
    wallet_config = configuration.get("wallet", {})
    if not wallet_config.get("address") and not wallet_config.get("contract_hash"):
        deny_codes.append("WALLET_CONFIGURATION_MISSING")

    # 8. Contract configuration check
    contract_config = configuration.get("contract", {})
    if not contract_config.get("hash"):
        deny_codes.append("CONTRACT_CONFIGURATION_MISSING")

    # Deduplicate
    deny_codes = sorted(set(deny_codes))

    result = {
        "allow": len(deny_codes) == 0,
        "deny_codes": deny_codes,
        "evaluated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "policy_version": POLICY_VERSION,
        "policy_hash": "",
    }

    # Hash the result
    result["policy_hash"] = sha256_hex(canonical_json({k: v for k, v in result.items() if k != "policy_hash"}))

    return result
