import os
os.environ["T3_MOCK"] = "true"

import uuid
import pytest
from src.terminal3_agent_auth_adapter import sign_action_request
from src.governed_action_gate import evaluate_action


def test_missing_proof():
    decision = evaluate_action({}, "READ_MEMORY")
    assert decision["decision"] == "DENY"


def test_garbage_signature(monkeypatch):
    # Build valid proof in mock mode, then corrupt sig fields and verify in live mode
    proof = sign_action_request("READ_MEMORY", uuid.uuid4().hex)
    proof["signature_hex"] = "deadbeef" * 16   # corrupt signature (right length, wrong value)
    proof["public_key_hex"] = "aa" * 32         # corrupt key -> payload_hash mismatch -> IDENTITY_INVALID
    monkeypatch.setenv("T3_MOCK", "false")
    decision = evaluate_action(proof, "READ_MEMORY")
    assert decision["decision"] == "DENY"
    assert decision["denial_code"] in ("IDENTITY_INVALID", "IDENTITY_MISSING")


def test_missing_nonce():
    proof = sign_action_request("READ_MEMORY", uuid.uuid4().hex)
    del proof["nonce"]
    decision = evaluate_action(proof, "READ_MEMORY")
    assert decision["decision"] == "DENY"
    assert decision["denial_code"] == "NONCE_MISSING"
