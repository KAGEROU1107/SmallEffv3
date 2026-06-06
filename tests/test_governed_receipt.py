"""
Unit tests for governed receipt generator.
"""

import pytest
from src.proposal_schema import build_proposal
from src.policy_engine import evaluate_policy
from src.governed_receipt import (
    build_receipt,
    verify_receipt_hash,
    sanitize_receipt,
)

VALID_RECIPIENT = "a" * 64


def _make_proposal(amount=5_000_000_000):
    result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, amount, "Test transfer")
    assert result["valid"]
    return result["proposal"]


def _make_confirmation(proposal_hash):
    return {
        "proposal_hash": proposal_hash,
        "confirmed": True,
        "confirmed_at": "2026-01-01T00:00:00Z",
        "confirmation_method": "test",
        "confirmation_hash": "",
    }


class TestGovernedReceipt:
    def test_receipt_builds(self):
        proposal = _make_proposal()
        confirmation = _make_confirmation(proposal["proposal_hash"])
        config = {
            "max_test_transfer_motes": 10_000_000_000,
            "approved_recipients": [VALID_RECIPIENT],
            "wallet": {"address": "0x" + "b" * 40},
            "contract": {"hash": "0x" + "c" * 64},
        }
        policy = evaluate_policy(proposal, confirmation, config)

        receipt = build_receipt(
            proposal=proposal,
            policy_result=policy,
            human_confirmation=confirmation,
            casper_network="casper-test",
            contract_hash="0x" + "c" * 64,
            entry_point="record_proposal",
            transaction_hash="0x" + "d" * 64,
            transaction_status="pending",
        )

        assert receipt["receipt_version"] == "1.0"
        assert receipt["proposal_hash"] == proposal["proposal_hash"]
        assert receipt["policy_hash"] == policy["policy_hash"]
        assert receipt["casper_network"] == "casper-test"
        assert receipt["receipt_hash"] != ""

    def test_receipt_hash_verification(self):
        proposal = _make_proposal()
        confirmation = _make_confirmation(proposal["proposal_hash"])
        config = {
            "max_test_transfer_motes": 10_000_000_000,
            "approved_recipients": [VALID_RECIPIENT],
            "wallet": {"address": "0x" + "b" * 40},
            "contract": {"hash": "0x" + "c" * 64},
        }
        policy = evaluate_policy(proposal, confirmation, config)

        receipt = build_receipt(proposal, policy, confirmation)
        assert verify_receipt_hash(receipt) is True

    def test_tampered_receipt_fails(self):
        proposal = _make_proposal()
        confirmation = _make_confirmation(proposal["proposal_hash"])
        config = {
            "max_test_transfer_motes": 10_000_000_000,
            "approved_recipients": [VALID_RECIPIENT],
            "wallet": {"address": "0x" + "b" * 40},
            "contract": {"hash": "0x" + "c" * 64},
        }
        policy = evaluate_policy(proposal, confirmation, config)

        receipt = build_receipt(proposal, policy, confirmation)
        receipt["transaction_hash"] = "tampered"
        assert verify_receipt_hash(receipt) is False

    def test_sanitized_receipt(self):
        proposal = _make_proposal()
        confirmation = _make_confirmation(proposal["proposal_hash"])
        config = {
            "max_test_transfer_motes": 10_000_000_000,
            "approved_recipients": [VALID_RECIPIENT],
            "wallet": {"address": "0x" + "b" * 40},
            "contract": {"hash": "0x" + "c" * 64},
        }
        policy = evaluate_policy(proposal, confirmation, config)

        receipt = build_receipt(proposal, policy, confirmation)
        safe = sanitize_receipt(receipt)

        assert "proposal_hash" in safe
        assert "receipt_hash" in safe
        assert len(safe) <= 12  # only safe fields

    def test_receipt_with_empty_transaction(self):
        """Receipt can be built before tx submission (pre-submission state)."""
        proposal = _make_proposal()
        confirmation = _make_confirmation(proposal["proposal_hash"])
        config = {
            "max_test_transfer_motes": 10_000_000_000,
            "approved_recipients": [VALID_RECIPIENT],
            "wallet": {"address": "0x" + "b" * 40},
            "contract": {"hash": "0x" + "c" * 64},
        }
        policy = evaluate_policy(proposal, confirmation, config)

        receipt = build_receipt(
            proposal, policy, confirmation,
            transaction_hash="",
            transaction_status="pre-submission",
        )
        assert receipt["transaction_hash"] == ""
        assert verify_receipt_hash(receipt) is True
