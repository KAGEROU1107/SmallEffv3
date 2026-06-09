import json
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.execution_receipt import build_receipt, verify_receipt
from src.governed_action_gate import evaluate_action
from src.terminal3_agent_auth_adapter import sign_action_request


def main() -> int:
    load_dotenv()
    os.environ["T3_MOCK"] = "false"

    if not os.getenv("T3N_API_KEY") and not os.getenv("TERMINAL3_API_KEY"):
        print("T3N token demo")
        print("  result : FAIL")
        print("  reason : T3N_API_KEY missing")
        return 1

    if not os.getenv("DID") and not os.getenv("T3N_DID"):
        print("T3N token demo")
        print("  result : FAIL")
        print("  reason : DID missing")
        return 1

    action = "READ_MEMORY"
    proof = sign_action_request(action, uuid.uuid4().hex)
    decision = evaluate_action(proof, action)
    receipt = build_receipt(decision)
    serialized_receipt = json.dumps(receipt, sort_keys=True)

    secret_prefix = (os.getenv("T3N_API_KEY") or os.getenv("TERMINAL3_API_KEY") or "")[:10]
    ok = (
        decision.get("decision") == "ALLOW"
        and proof.get("did") in (os.getenv("DID"), os.getenv("T3N_DID"))
        and verify_receipt(receipt)
        and secret_prefix not in serialized_receipt
    )

    print("T3N token demo")
    print(f"  result       : {'PASS' if ok else 'FAIL'}")
    print(f"  mock_mode    : {os.getenv('T3_MOCK')}")
    print(f"  did_bound    : {bool(proof.get('did'))}")
    print(f"  proof_signed : {len(proof.get('signature_hex', '')) == 128}")
    print(f"  decision     : {decision.get('decision')}")
    print(f"  receipt_ok   : {verify_receipt(receipt)}")
    print(f"  no_secret    : {secret_prefix not in serialized_receipt}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
