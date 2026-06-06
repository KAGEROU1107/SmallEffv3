"""
Unit tests for human confirmation.
"""

import pytest
from src.proposal_schema import build_proposal
from src.human_confirmation import (
    build_human_confirmation,
    verify_confirmation,
    display_proposal_for_review,
)

VALID_RECIPIENT = "a" * 64


class TestHumanConfirmation:
    def test_build_confirmation(self):
        conf = build_human_confirmation("abc123", confirmed=True)
        assert conf["confirmed"] is True
        assert conf["proposal_hash"] == "abc123"
        assert conf["confirmation_hash"] != ""
        assert conf["confirmed_at"] != ""

    def test_rejected_confirmation(self):
        conf = build_human_confirmation("abc123", confirmed=False)
        assert conf["confirmed"] is False
        assert conf["confirmed_at"] == ""

    def test_verify_valid_confirmation(self):
        conf = build_human_confirmation("abc123", confirmed=True)
        errors = verify_confirmation(conf, "abc123")
        assert errors == []

    def test_verify_unconfirmed(self):
        conf = build_human_confirmation("abc123", confirmed=False)
        errors = verify_confirmation(conf, "abc123")
        assert "CONFIRMATION_NOT_CONFIRMED" in errors

    def test_verify_wrong_hash(self):
        conf = build_human_confirmation("abc123", confirmed=True)
        errors = verify_confirmation(conf, "wrong-hash")
        assert "CONFIRMATION_HASH_MISMATCH" in errors

    def test_verify_tampered(self):
        conf = build_human_confirmation("abc123", confirmed=True)
        conf["proposal_hash"] = "tampered"
        errors = verify_confirmation(conf, "abc123")
        assert "CONFIRMATION_TAMPERED" in errors

    def test_display_proposal(self):
        result = build_proposal("TRANSFER_CSPR", VALID_RECIPIENT, 5_000_000_000, "Test")
        proposal = result["proposal"]
        display = display_proposal_for_review(proposal)
        assert "TRANSFER_CSPR" in display
        assert "5.000000000" in display
        assert proposal["proposal_hash"] in display
