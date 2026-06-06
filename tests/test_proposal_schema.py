"""
Unit tests for proposal schema.
"""

import pytest
from src.proposal_schema import (
    build_proposal,
    verify_proposal_hash,
    validate_recipient,
    validate_amount,
    canonical_json,
    sha256_hex,
    ALLOWED_ACTIONS,
    ALLOWED_NETWORKS,
    proposal_to_cspr_amount,
)

VALID_RECIPIENT = "a" * 64  # 64 hex chars


class TestBuildProposal:
    def test_valid_proposal(self):
        result = build_proposal(
            action="TRANSFER_CSPR",
            recipient=VALID_RECIPIENT,
            amount_motes=5_000_000_000,
            reason="Test transfer",
        )
        assert result["valid"] is True
        assert "proposal" in result
        p = result["proposal"]
        assert p["action"] == "TRANSFER_CSPR"
        assert p["recipient"] == VALID_RECIPIENT
        assert p["amount_motes"] == "5000000000"
        assert p["network"] == "casper-test"
        assert p["proposal_hash"] != ""

    def test_proposal_hash_verification(self):
        result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, 1000, "test")
        assert result["valid"] is True
        assert verify_proposal_hash(result["proposal"]) is True

    def test_tampered_proposal_fails_hash(self):
        result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, 1000, "test")
        result["proposal"]["amount_motes"] = "999999999999"
        assert verify_proposal_hash(result["proposal"]) is False

    def test_unsupported_action(self):
        result = build_proposal("DELETE_ACCOUNT", VALID_RECIPIENT, 1000, "test")
        assert result["valid"] is False
        assert "ACTION_NOT_ALLOWED" in result["errors"]

    def test_wrong_network(self):
        result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, 1000, "test", network="casper")
        assert result["valid"] is False
        assert "NETWORK_NOT_ALLOWED" in result["errors"]

    def test_invalid_recipient(self):
        result = build_proposal("TRANSFER_CSPR", "not-hex-enough", 1000, "test")
        assert result["valid"] is False
        assert "RECIPIENT_INVALID" in result["errors"]

    def test_empty_recipient(self):
        result = build_proposal("TRANSFER_CSPR", "", 1000, "test")
        assert result["valid"] is False

    def test_zero_amount(self):
        result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, 0, "test")
        assert result["valid"] is False
        assert "AMOUNT_INVALID" in result["errors"]

    def test_negative_amount(self):
        result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, -100, "test")
        assert result["valid"] is False
        assert "AMOUNT_INVALID" in result["errors"]

    def test_float_amount(self):
        result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, 1.5, "test")
        assert result["valid"] is False
        assert "AMOUNT_INVALID" in result["errors"]

    def test_string_amount_valid(self):
        result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, "5000000000", "test")
        assert result["valid"] is True

    def test_string_amount_invalid(self):
        result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, "not-a-number", "test")
        assert result["valid"] is False

    def test_reason_too_long(self):
        long_reason = "x" * 600
        result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, 1000, long_reason)
        assert result["valid"] is False
        assert "REASON_TOO_LONG" in result["errors"]

    def test_empty_reason(self):
        result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, 1000, "")
        assert result["valid"] is False
        assert "REASON_EMPTY" in result["errors"]

    def test_cspr_conversion(self):
        assert proposal_to_cspr_amount(5_000_000_000) == 5.0
        assert proposal_to_cspr_amount(1) == 0.000000001
        assert proposal_to_cspr_amount(1_000_000_000) == 1.0

    def test_canonical_json_deterministic(self):
        d = {"b": "2", "a": "1", "c": "3"}
        assert canonical_json(d) == '{"a":"1","b":"2","c":"3"}'


class TestValidateRecipient:
    def test_valid_hex(self):
        assert validate_recipient("a" * 64) == []

    def test_too_short(self):
        assert len(validate_recipient("a" * 32)) > 0

    def test_non_hex(self):
        assert len(validate_recipient("g" * 64)) > 0

    def test_empty(self):
        assert len(validate_recipient("")) > 0


class TestValidateAmount:
    def test_valid(self):
        assert validate_amount(1000) == []

    def test_zero(self):
        assert len(validate_amount(0)) > 0

    def test_negative(self):
        assert len(validate_amount(-1)) > 0

    def test_bool(self):
        assert len(validate_amount(True)) > 0

    def test_float(self):
        assert len(validate_amount(1.5)) > 0

    def test_none(self):
        assert len(validate_amount(None)) > 0
