import os
import sys
import uuid
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

if "T3_MOCK" not in os.environ:
    os.environ["T3_MOCK"] = "true"

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.terminal3_agent_auth_adapter import sign_action_request
from src.governed_action_gate import evaluate_action
from src.execution_receipt import build_receipt, save_receipt, verify_receipt

PASS = "[PASS]"
FAIL = "[FAIL]"

results = []


def header(n, title):
    print(f"\n{'='*60}")
    print(f"  SCENARIO {n}: {title}")
    print(f"{'='*60}")


def report(tag, decision, receipt=None):
    ok = True
    code = decision.get("denial_code") or "-"
    print(f"  Decision : {decision['decision']}  (denial_code={code})")
    if receipt:
        print(f"  Receipt  : {receipt['receipt_id']}")
        print(f"  Integrity: {'OK' if verify_receipt(receipt) else 'FAIL'}")
        print(f"  No secrets: {not receipt.get('raw_secret_included', True)}")
    return ok


# ─── Scenario 1: Valid agent → READ_MEMORY → ALLOW ──────────────────────────
header(1, "Valid agent -> READ_MEMORY -> ALLOW")
nonce1 = uuid.uuid4().hex
proof1 = sign_action_request("READ_MEMORY", nonce1)
d1 = evaluate_action(proof1, "READ_MEMORY")
r1 = build_receipt(d1)
save_receipt(r1)
ok1 = d1["decision"] == "ALLOW" and verify_receipt(r1)
print(f"  {PASS if ok1 else FAIL}", end="  ")
report("s1", d1, r1)
results.append(ok1)

# ─── Scenario 2: Valid agent → POLICY_MODIFY → DENY ACTION_FORBIDDEN ────────
header(2, "Valid agent -> POLICY_MODIFY -> DENY ACTION_FORBIDDEN")
nonce2 = uuid.uuid4().hex
proof2 = sign_action_request("POLICY_MODIFY", nonce2)
d2 = evaluate_action(proof2, "POLICY_MODIFY")
r2 = build_receipt(d2)
save_receipt(r2)
ok2 = d2["decision"] == "DENY" and d2["denial_code"] == "ACTION_FORBIDDEN"
print(f"  {PASS if ok2 else FAIL}", end="  ")
report("s2", d2, r2)
results.append(ok2)

# ─── Scenario 3: Invalid identity → DENY ────────────────────────────────────
header(3, "Invalid/missing identity -> DENY")
# Provide a nonce but no identity fields -> IDENTITY_MISSING
d3 = evaluate_action({"nonce": uuid.uuid4().hex}, "READ_MEMORY")
r3 = build_receipt(d3)
ok3 = d3["decision"] == "DENY" and d3["denial_code"] in ("IDENTITY_MISSING", "IDENTITY_INVALID", "NONCE_MISSING")
print(f"  {PASS if ok3 else FAIL}", end="  ")
report("s3", d3)
results.append(ok3)

# ─── Scenario 4: Nonce replay → second attempt DENY NONCE_REPLAYED ──────────
header(4, "Nonce replay -> second attempt DENY NONCE_REPLAYED")
shared_nonce = uuid.uuid4().hex
proof4a = sign_action_request("READ_MEMORY", shared_nonce)
d4a = evaluate_action(proof4a, "READ_MEMORY")

proof4b = sign_action_request("LIST_SKILLS", shared_nonce)
d4b = evaluate_action(proof4b, "LIST_SKILLS")

ok4 = d4a["decision"] == "ALLOW" and d4b["decision"] == "DENY" and d4b["denial_code"] == "NONCE_REPLAYED"
print(f"  First attempt  : {d4a['decision']}")
print(f"  Second attempt : {d4b['decision']} ({d4b['denial_code']})")
print(f"  {PASS if ok4 else FAIL}")
results.append(ok4)

# ─── Scenario 5: Receipt inspection → no secrets ────────────────────────────
header(5, "Receipt inspection -> no raw secrets, hash intact")
ok5 = (
    not r1.get("raw_secret_included", True)
    and verify_receipt(r1)
    and "TERMINAL3_API_KEY" not in json.dumps(r1)
    and "0xdd" not in json.dumps(r1)
)
print(f"  raw_secret_included : {r1.get('raw_secret_included')}")
print(f"  receipt_hash valid  : {verify_receipt(r1)}")
print(f"  {PASS if ok5 else FAIL}")
results.append(ok5)

# ─── Summary ─────────────────────────────────────────────────────────────────
passed = sum(results)
print(f"\n{'='*60}")
print(f"  SUMMARY: {passed}/5 scenarios passed")
print(f"{'='*60}\n")

sys.exit(0 if passed == 5 else 1)
