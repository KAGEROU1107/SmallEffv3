import os
os.environ["T3_MOCK"] = "true"
import uuid
from src.terminal3_agent_auth_adapter import sign_action_request
from src.governed_action_gate import evaluate_action
from src.execution_receipt import build_receipt, verify_receipt

def test_valid_read_action():
    nonce = uuid.uuid4().hex
    proof = sign_action_request("READ_MEMORY", nonce)
    decision = evaluate_action(proof, "READ_MEMORY")
    assert decision["decision"] == "ALLOW"
    receipt = build_receipt(decision)
    assert receipt["raw_secret_included"] == False
    assert verify_receipt(receipt) == True
    assert receipt["agent_fingerprint"] is not None