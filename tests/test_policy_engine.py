"""
Unit tests for deterministic policy engine.
"""

import pytest
from src.proposal_schema import build_proposal
from src.policy_engine import evaluate_policy, DENIAL_CODES

VALID_RECIPIENT = "a" * 64


def _make_proposal(amount=5_000_000_000, recipient=VALID_RECIPIENT, network="casper-test"):
    result = build_proposal("TRANSFER_CSPR", recipient, amount, "Test transfer", network=network)
    assert result["valid"], f"Proposal invalid: {result.get('errors')}"
    return result["proposal"]


def _make_confirmation(proposal_hash):
    return {
        "proposal_hash": proposal_hash,
        "confirmed": True,
        "confirmed_at": "2026-01-01T00:00:00Z",
        "confirmation_method": "test",
        "confirmation_hash": "",
    }


class TestPolicyEngine:
    def test_valid_proposal_passes(self):
        proposal = _make_proposal()
        confirmation = _make_confirmation(proposal["proposal_hash"])
        config = {
            "max_test_transfer_motes": 10_000_000_000,
            "approved_recipients": [VALID_RECIPIENT],
            "wallet": {"address": "0x" + "b" * 40},
            "contract": {"hash": "0x" + "c" * 64},
        }
        result = evaluate_policy(proposal, confirmation, config)
        assert result["allow"] is True
        assert result["deny_codes"] == []

    def test_action_not_allowed(self):
        proposal = _make_proposal()
        proposal["action"] = "DELETE_EVERYTHING"
        confirmation = _make_confirmation(proposal["proposal_hash"])
        result = evaluate_policy(proposal, confirmation, {})
        assert result["allow"] is False
        assert "ACTION_NOT_ALLOWED" in result["deny_codes"]

    def test_network_not_allowed(self):
        proposal = _make_proposal()
        proposal["network"] = "casper"
        confirmation = _make_confirmation(proposal["proposal_hash"])
        result = evaluate_policy(proposal, confirmation, {})
        assert result["allow"] is False
        assert "NETWORK_NOT_ALLOWED" in result["deny_codes"]

    def test_recipient_invalid(self):
        proposal = _make_proposal()
        proposal["recipient"] = "too-short"
        confirmation = _make_confirmation(proposal["proposal_hash"])
        result = evaluate_policy(proposal, confirmation, {})
        assert result["allow"] is False
        assert "RECIPIENT_INVALID" in result["deny_codes"]

    def test_recipient_not_approved(self):
        proposal = _make_proposal(recipient="b" * 64)
        confirmation = _make_confirmation(proposal["proposal_hash"])
        config = {"approved_recipients": [VALID_RECIPIENT]}
        result = evaluate_policy(proposal, confirmation, config)
        assert result["allow"] is False
        assert "RECIPIENT_NOT_APPROVED" in result["deny_codes"]

    def test_amount_zero(self):
        proposal = _make_proposal()
        proposal["amount_motes"] = "0"
        confirmation = _make_confirmation(proposal["proposal_hash"])
        result = evaluate_policy(proposal, confirmation, {})
        assert result["allow"] is False
        assert "AMOUNT_INVALID" in result["deny_codes"]

    def test_amount_negative(self):
        proposal = _make_proposal()
        proposal["amount_motes"] = "-100"
        confirmation = _make_confirmation(proposal["proposal_hash"])
        result = evaluate_policy(proposal, confirmation, {})
        assert result["allow"] is False
        assert "AMOUNT_INVALID" in result["deny_codes"]

    def test_amount_exceeds_limit(self):
        proposal = _make_proposal(amount=99_000_000_000)
        confirmation = _make_confirmation(proposal["proposal_hash"])
        config = {"max_test_transfer_motes": 10_000_000_000}
        result = evaluate_policy(proposal, confirmation, config)
        assert result["allow"] is False
        assert "AMOUNT_EXCEEDS_LIMIT" in result["deny_codes"]

    def test_proposal_hash_tampered(self):
        proposal = _make_proposal()
        proposal["amount_motes"] = "999999999999"  # tamper
        confirmation = _make_confirmation(proposal["proposal_hash"])
        result = evaluate_policy(proposal, confirmation, {})
        assert result["allow"] is False
        assert "PROPOSAL_HASH_INVALID" in result["deny_codes"]

    def test_missing_human_confirmation(self):
        proposal = _make_proposal()
        result = evaluate_policy(proposal, None, {})
        assert result["allow"] is False
        assert "HUMAN_CONFIRMATION_MISSING" in result["deny_codes"]

    def test_human_rejected(self):
        proposal = _make_proposal()
        confirmation = _make_confirmation(proposal["proposal_hash"])
        confirmation["confirmed"] = False
        result = evaluate_policy(proposal, confirmation, {})
        assert result["allow"] is False
        assert "HUMAN_CONFIRMATION_MISSING" in result["deny_codes"]

    def test_wrong_confirmation_hash(self):
        proposal = _make_proposal()
        confirmation = _make_confirmation("wrong-hash-" * 4)
        result = evaluate_policy(proposal, confirmation, {})
        assert result["allow"] is False
        assert "HUMAN_CONFIRMATION_MISSING" in result["deny_codes"]

    def test_missing_wallet_config(self):
        proposal = _make_proposal()
        confirmation = _make_confirmation(proposal["proposal_hash"])
        config = {"contract": {"hash": "0x" + "c" * 64}}
        result = evaluate_policy(proposal, confirmation, config)
        assert result["allow"] is False
        assert "WALLET_CONFIGURATION_MISSING" in result["deny_codes"]

    def test_missing_contract_config(self):
        proposal = _make_proposal()
        confirmation = _make_confirmation(proposal["proposal_hash"])
        config = {"wallet": {"address": "0x" + "b" * 40}}
        result = evaluate_policy(proposal, confirmation, config)
        assert result["allow"] is False
        assert "CONTRACT_CONFIGURATION_MISSING" in result["deny_codes"]

    def test_policy_hash_present(self):
        proposal = _make_proposal()
        confirmation = _make_confirmation(proposal["proposal_hash"])
        config = {
            "max_test_transfer_motes": 10_000_000_000,
            "approved_recipients": [VALID_RECIPIENT],
            "wallet": {"address": "0x" + "b" * 40},
            "contract": {"hash": "0x" + "c" * 64},
        }
        result = evaluate_policy(proposal, confirmation, config)
        assert result["policy_hash"] != ""
        assert len(result["policy_hash"]) == 64  # sha256 hex

    def test_mainnet_rejected(self):
        proposal = _make_proposal()
        proposal["network"] = "casper"
        confirmation = _make_confirmation(proposal["proposal_hash"])
        result = evaluate_policy(proposal, confirmation, {})
        assert "NETWORK_NOT_ALLOWED" in result["deny_codes"]
