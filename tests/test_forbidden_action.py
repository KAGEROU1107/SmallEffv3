import os
os.environ["T3_MOCK"] = "true"

import uuid
from src.terminal3_agent_auth_adapter import sign_action_request
from src.governed_action_gate import evaluate_action


def test_policy_modify_denied():
    proof = sign_action_request("POLICY_MODIFY", uuid.uuid4().hex)
    decision = evaluate_action(proof, "POLICY_MODIFY")
    assert decision["decision"] == "DENY"
    assert decision["denial_code"] == "ACTION_FORBIDDEN"


def test_persona_write_denied():
    proof = sign_action_request("PERSONA_WRITE", uuid.uuid4().hex)
    decision = evaluate_action(proof, "PERSONA_WRITE")
    assert decision["decision"] == "DENY"
    assert decision["denial_code"] == "ACTION_FORBIDDEN"


def test_unknown_action_denied():
    proof = sign_action_request("UNKNOWN_ACTION_XYZ", uuid.uuid4().hex)
    decision = evaluate_action(proof, "UNKNOWN_ACTION_XYZ")
    assert decision["decision"] == "DENY"
    assert decision["denial_code"] == "ACTION_FORBIDDEN"
