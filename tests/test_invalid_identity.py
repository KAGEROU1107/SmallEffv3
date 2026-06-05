import os
import uuid
import pytest
from src.governed_action_gate import evaluate_action

os.environ["T3_MOCK"] = "true"

def test_missing_proof():
    decision = evaluate_action({}, "READ_MEMORY")
    assert decision["decision"] == "DENY"

def test_garbage_signature(monkeypatch):
    # Must run in live mode — mock bypasses crypto, defeating the test
    monkeypatch.setenv("T3_MOCK", "false")
    proof = {
        "public_key_hex": "aa" * 32,
        "signature_hex": "bb" * 64,
        "challenge_hex": "cc" * 32,
        "agent_id": "fake",
        "nonce": uuid.uuid4().hex,
    }
    decision = evaluate_action(proof, "READ_MEMORY")
    assert decision["decision"] == "DENY"
    assert decision["denial_code"] in ("IDENTITY_INVALID", "IDENTITY_MISSING")

def test_no_nonce_allowed():
    proof = {
        "public_key_hex": "aa" * 32,
        "signature_hex": "bb" * 64,
        "challenge_hex": "cc" * 32,
        "agent_id": "agent-123"
    }
    decision = evaluate_action(proof, "READ_MEMORY")
    assert decision["decision"] == "ALLOW"
    assert "nonce_consumed" in decision
    assert decision["nonce_consumed"] is not None
    assert decision["denial_code"] is None