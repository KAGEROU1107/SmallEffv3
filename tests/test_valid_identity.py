import os
os.environ["T3_MOCK"] = "true"

import uuid
from src.terminal3_agent_auth_adapter import sign_challenge
from src.governed_action_gate import evaluate_action
from src.execution_receipt import build_receipt, verify_receipt

def test_valid_read_action():
    challenge = os.urandom(32)
    proof = sign_challenge(challenge)
    proof["nonce"] = uuid.uuid4().hex
    decision = evaluate_action(proof, "READ_MEMORY")
    assert decision["decision"] == "ALLOW"
    receipt = build_receipt(decision)
    assert receipt["raw_secret_included"] == False
    assert verify_receipt(receipt) == True
    assert receipt["agent_fingerprint"] is not None