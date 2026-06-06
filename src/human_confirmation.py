"""
SmallEFFV3 Part 2 — Human Confirmation

Handles the human review and approval step.
No transaction may proceed without a valid confirmation record.
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from typing import Any

from src.proposal_schema import canonical_json, sha256_hex, proposal_to_cspr_amount


def display_proposal_for_review(proposal: dict[str, Any]) -> str:
    """Format a proposal for human review."""
    amount_cspr = proposal_to_cspr_amount(int(proposal.get("amount_motes", 0)))

    lines = [
        "╔══════════════════════════════════════════════════════════╗",
        "║  PROPOSAL REVIEW                                        ║",
        "╠══════════════════════════════════════════════════════════╣",
        f"║  Action:       {proposal.get('action', 'N/A'):<40} ║",
        f"║  Recipient:    {proposal.get('recipient', 'N/A')[:40]:<40} ║",
        f"║  Amount:       {amount_cspr:.9f} CSPR{' ' * (30 - len(f'{amount_cspr:.9f}'))} ║",
        f"║  Amount motes: {proposal.get('amount_motes', 'N/A'):<40} ║",
        f"║  Network:      {proposal.get('network', 'N/A'):<40} ║",
        f"║  Reason:       {proposal.get('reason', 'N/A')[:40]:<40} ║",
        "╠══════════════════════════════════════════════════════════╣",
        "╠══════════════════════════════════════════════════════════╣",
        "╚══════════════════════════════════════════════════════════╝",
    ]
    lines.append(f"Proposal Hash: {proposal.get('proposal_hash', 'N/A')}")
    return "\n".join(lines)


def build_human_confirmation(
    proposal_hash: str,
    confirmed: bool,
    confirmation_method: str = "cli",
) -> dict[str, Any]:
    """
    Build a human confirmation record.

    The confirmation binds to the proposal hash — confirming one proposal
    does not authorize another.
    """
    confirmed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    record = {
        "proposal_hash": proposal_hash,
        "confirmed": confirmed,
        "confirmed_at": confirmed_at if confirmed else "",
        "confirmation_method": confirmation_method,
        "confirmation_hash": "",
    }

    # Hash the confirmation
    record["confirmation_hash"] = sha256_hex(
        canonical_json({k: v for k, v in record.items() if k != "confirmation_hash"})
    )

    return record


def verify_confirmation(confirmation: dict[str, Any], proposal_hash: str) -> list[str]:
    """Verify a confirmation record is valid and matches the proposal."""
    errors = []

    if not confirmation.get("confirmed"):
        errors.append("CONFIRMATION_NOT_CONFIRMED")

    if confirmation.get("proposal_hash", "") != proposal_hash:
        errors.append("CONFIRMATION_HASH_MISMATCH")

    # Verify integrity
    stored_hash = confirmation.get("confirmation_hash", "")
    computed = sha256_hex(
        canonical_json({k: v for k, v in confirmation.items() if k != "confirmation_hash"})
    )
    if stored_hash != computed:
        errors.append("CONFIRMATION_TAMPERED")

    return errors


def cli_confirm(proposal: dict[str, Any]) -> dict[str, Any]:
    """
    Interactive CLI confirmation flow.
    Returns a confirmation record.
    """
    print(display_proposal_for_review(proposal))
    print()
    print("Type the full proposal hash to confirm, or 'reject' to cancel:")
    print(f"  Proposal hash: {proposal.get('proposal_hash', '')}")
    print()

    user_input = input("> ").strip()

    if user_input == proposal.get("proposal_hash", ""):
        print("✓ Confirmed.")
        return build_human_confirmation(
            proposal_hash=proposal["proposal_hash"],
            confirmed=True,
            confirmation_method="cli",
        )
    else:
        print("✗ Rejected.")
        return build_human_confirmation(
            proposal_hash=proposal["proposal_hash"],
            confirmed=False,
            confirmation_method="cli",
        )
