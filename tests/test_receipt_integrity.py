import os
os.environ["T3_MOCK"] = "true"

import uuid
from src.terminal3_agent_auth_adapter import sign_action_request
from src.governed_action_gate import evaluate_action
from src.execution_receipt import build_receipt, verify_receipt


def _allow_receipt():
    proof = sign_action_request("READ_MEMORY", uuid.uuid4().hex)
    decision = evaluate_action(proof, "READ_MEMORY")
    return build_receipt(decision)


def _deny_receipt():
    proof = sign_action_request("POLICY_MODIFY", uuid.uuid4().hex)
    decision = evaluate_action(proof, "POLICY_MODIFY")
    return build_receipt(decision)


def test_tampered_action_fails_verification():
    receipt = _allow_receipt()
    assert verify_receipt(receipt) is True
    receipt["action"] = "POLICY_MODIFY"  # mutate after hashing
    assert verify_receipt(receipt) is False


def test_tampered_decision_fails_verification():
    receipt = _allow_receipt()
    receipt["decision"] = "ALLOW_OVERRIDE"
    assert verify_receipt(receipt) is False


def test_deny_receipt_no_secrets():
    receipt = _deny_receipt()
    assert receipt["raw_secret_included"] is False
    assert receipt["denial_code"] == "ACTION_FORBIDDEN"
    assert verify_receipt(receipt) is True


def test_fingerprint_does_not_contain_raw_key():
    api_key = os.getenv("TERMINAL3_API_KEY", "")
    receipt = _allow_receipt()
    fp = receipt.get("agent_fingerprint", "")
    assert fp is not None
    assert len(fp) > 0
    # fingerprint must not be the raw key or any 8+ char prefix of it
    if len(api_key) > 8:
        assert api_key[:8] not in fp
    assert "0xdd" not in fp
