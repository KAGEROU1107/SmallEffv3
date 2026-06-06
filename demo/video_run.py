"""
video_run.py — Self-narrating demo for screen recording.
Run this, hit record, done. No audio needed.
"""
import os
import sys
import time
import json
import uuid
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

os.environ.setdefault("T3_MOCK", "true")
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.terminal3_agent_auth_adapter import sign_action_request
from src.governed_action_gate import evaluate_action
from src.execution_receipt import build_receipt, save_receipt, verify_receipt

W = 62

def cls():
    subprocess.run(["cls"] if os.name == "nt" else ["clear"], shell=(os.name == "nt"))

def bar(char="═"):
    return char * W

def box(*lines, char="═"):
    inner = W - 2
    print("╔" + bar(char) + "╗")
    for line in lines:
        padded = line.ljust(inner)
        print("║ " + padded + " ║")
    print("╚" + bar(char) + "╝")

def pause(n):
    time.sleep(n)

def title_card(heading, *body_lines, wait=3):
    cls()
    print()
    box(heading, "", *body_lines)
    print()
    pause(wait)

def section(n, title):
    print()
    print("┌" + "─" * W + "┐")
    print(f"│  SCENE {n}: {title:<{W - 10}}│")
    print("└" + "─" * W + "┘")
    print()
    pause(1)


# ─── SCENE 0: Title ──────────────────────────────────────────────────────────
title_card(
    "  Verifiable Governed Agent Gateway",
    "  Terminal 3 Agent Auth — DoraHacks Bounty",
    "",
    "  What this solves:",
    "  AI agents have no verifiable identity.",
    "  Fake agents can impersonate real ones.",
    "  Replay attacks go undetected.",
    "  Actions leave no tamper-proof trail.",
    "",
    "  This prototype fixes all four.",
    wait=5,
)

# ─── SCENE 1: Architecture ───────────────────────────────────────────────────
title_card(
    "  Architecture",
    "",
    "  Agent (Ed25519 key)",
    "        │",
    "        ▼",
    "  terminal3_agent_auth_adapter.py   ← identity proof",
    "        │",
    "        ▼",
    "  governed_action_gate.py           ← policy + replay guard",
    "        │",
    "        ▼",
    "  execution_receipt.py              ← hash-bound receipt",
    "        │",
    "        ▼",
    "  ALLOW  or  DENY (with code)",
    wait=6,
)

# ─── SCENE 2: Demo ───────────────────────────────────────────────────────────
cls()
section(1, "Running 5 live scenarios")

print("  Each scenario tests a real security property.")
print("  Crypto: Ed25519 (cryptography library)")
print("  Nonce store: atomic filesystem lock (open x-mode)")
print("  Receipts: sha256-bound JSON")
print()
pause(2)
print("  $ python demo/run_demo.py")
print()
pause(1)

print("─" * W)

# Scenario 1
print()
print("  SCENARIO 1  Valid agent → READ_MEMORY")
print("  Expected   : ALLOW")
print()
pause(1)

nonce1 = uuid.uuid4().hex
proof1 = sign_action_request("READ_MEMORY", nonce1)
d1 = evaluate_action(proof1, "READ_MEMORY")
r1 = build_receipt(d1)
save_receipt(r1)
ok1 = d1["decision"] == "ALLOW" and verify_receipt(r1)

print(f"  Decision         : {d1['decision']}")
print(f"  denial_code      : {d1.get('denial_code') or '—'}")
print(f"  Receipt          : {r1['receipt_id']}")
print(f"  Receipt valid    : {verify_receipt(r1)}")
print(f"  No secrets       : {not r1.get('raw_secret_included', True)}")
print(f"  Result           : {'✓ PASS' if ok1 else '✗ FAIL'}")
pause(3)

# Scenario 2
print()
print("─" * W)
print()
print("  SCENARIO 2  Valid agent → POLICY_MODIFY")
print("  Expected   : DENY  ACTION_FORBIDDEN")
print()
pause(1)

nonce2 = uuid.uuid4().hex
proof2 = sign_action_request("POLICY_MODIFY", nonce2)
d2 = evaluate_action(proof2, "POLICY_MODIFY")
r2 = build_receipt(d2)
save_receipt(r2)
ok2 = d2["decision"] == "DENY" and d2["denial_code"] == "ACTION_FORBIDDEN"

print(f"  Decision         : {d2['decision']}")
print(f"  denial_code      : {d2.get('denial_code') or '—'}")
print(f"  Policy blocked it — agent stopped cold.")
print(f"  Result           : {'✓ PASS' if ok2 else '✗ FAIL'}")
pause(3)

# Scenario 3
print()
print("─" * W)
print()
print("  SCENARIO 3  No API key / missing identity")
print("  Expected   : DENY  IDENTITY_MISSING")
print()
pause(1)

d3 = evaluate_action({"nonce": uuid.uuid4().hex}, "READ_MEMORY")
r3 = build_receipt(d3)
ok3 = d3["decision"] == "DENY" and d3["denial_code"] in (
    "IDENTITY_MISSING", "IDENTITY_INVALID", "NONCE_MISSING"
)

print(f"  Decision         : {d3['decision']}")
print(f"  denial_code      : {d3.get('denial_code') or '—'}")
print(f"  No key = no trust. Gate refuses immediately.")
print(f"  Result           : {'✓ PASS' if ok3 else '✗ FAIL'}")
pause(3)

# Scenario 4
print()
print("─" * W)
print()
print("  SCENARIO 4  Replay attack — same nonce used twice")
print("  Expected   : first ALLOW, second DENY NONCE_REPLAYED")
print()
pause(1)

shared_nonce = uuid.uuid4().hex
proof4a = sign_action_request("READ_MEMORY", shared_nonce)
d4a = evaluate_action(proof4a, "READ_MEMORY")

proof4b = sign_action_request("LIST_SKILLS", shared_nonce)
d4b = evaluate_action(proof4b, "LIST_SKILLS")

ok4 = (
    d4a["decision"] == "ALLOW"
    and d4b["decision"] == "DENY"
    and d4b["denial_code"] == "NONCE_REPLAYED"
)

print(f"  Attempt 1        : {d4a['decision']}")
print(f"  Attempt 2        : {d4b['decision']}  ({d4b.get('denial_code')})")
print(f"  FileExistsError on nonce file = replay shield.")
print(f"  Result           : {'✓ PASS' if ok4 else '✗ FAIL'}")
pause(3)

# Scenario 5
print()
print("─" * W)
print()
print("  SCENARIO 5  Receipt inspection — no secrets, hash intact")
print()
pause(1)

ok5 = (
    not r1.get("raw_secret_included", True)
    and verify_receipt(r1)
    and "TERMINAL3_API_KEY" not in json.dumps(r1)
)

print(f"  raw_secret_included : {r1.get('raw_secret_included')}")
print(f"  receipt_hash valid  : {verify_receipt(r1)}")
print(f"  API key in receipt  : {'YES — BUG' if 'TERMINAL3_API_KEY' in json.dumps(r1) else 'No'}")
print(f"  Result              : {'✓ PASS' if ok5 else '✗ FAIL'}")
pause(3)

# Summary
passed = sum([ok1, ok2, ok3, ok4, ok5])
print()
print("═" * W)
print(f"  DEMO SUMMARY: {passed}/5 scenarios passed")
print("═" * W)
pause(3)

# ─── SCENE 3: Show a receipt ─────────────────────────────────────────────────
cls()
section(2, "Receipt file — hash-bound, no secrets")

receipt_files = sorted(Path("demo/sample_sanitized_receipts").glob("effv3-receipt-*.json"))
if receipt_files:
    latest = receipt_files[-1]
    print(f"  File: {latest.name}")
    print()
    data = json.loads(latest.read_text())
    for k, v in data.items():
        if k == "receipt_hash":
            print(f"  {k:<26}: {str(v)[:40]}...")
        else:
            print(f"  {k:<26}: {v}")
    print()
    print("  → agent_fingerprint is sha256[:12] of key — raw key never stored")
    print("  → receipt_hash covers all fields — tamper = hash mismatch")
    print("  → raw_secret_included = False — nothing sensitive in the file")
else:
    print("  (no receipt files found — run demo/run_demo.py first)")

pause(5)

# ─── SCENE 4: Tests ──────────────────────────────────────────────────────────
cls()
section(3, "Running test suite — pytest")

print("  $ python -m pytest tests/ -v")
print()
pause(1)

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
    capture_output=False,
)
print()
if result.returncode == 0:
    print("  ✓ All tests pass.")
else:
    print("  ✗ Some tests failed.")
pause(4)

# ─── SCENE 5: End card ───────────────────────────────────────────────────────
title_card(
    "  What is REAL vs MOCKED",
    "",
    "  REAL (cryptography library + filesystem):",
    "  ✓ Ed25519 key derivation from API key",
    "  ✓ Ed25519 signing + verification",
    "  ✓ Atomic nonce store (open x-mode → FileExistsError)",
    "  ✓ sha256 hash-bound receipts",
    "  ✓ Policy enforcement (ALLOW / DENY)",
    "",
    "  MOCKED (T3_MOCK=true for this demo):",
    "  • Terminal 3 live API endpoint calls",
    "  • Real API key (fixture used instead)",
    "",
    "  Core security properties are live — not simulated.",
    wait=7,
)

title_card(
    "  Verifiable Governed Agent Gateway",
    "",
    "  Terminal 3 Agent Auth Bounty — DoraHacks",
    "",
    "  Ed25519 identity  ·  Policy gate  ·  Replay shield",
    "  Hash-bound receipts  ·  Zero secret leakage",
    "",
    "  github.com/KAGEROU1107/SmallEffv3",
    wait=6,
)

print("  Done. Stop recording.")
