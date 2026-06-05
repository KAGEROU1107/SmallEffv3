"""
EFFV3 Hackathon Build Orchestrator
Boss dispatches persona-injected ILMU workers in parallel.
Each persona writes their domain module.
"""
import os
import json
import requests
import concurrent.futures
from pathlib import Path

ILMU_URL = "https://api.ilmu.ai/v1/chat/completions"
ILMU_KEY = os.getenv("ILMUCHAT_API_KEY", "")
ILMU_MODEL = "nemo-super"
TIMEOUT = 300

BASE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Persona definitions (injected as system context into each ILMU call)
# ---------------------------------------------------------------------------

EXIA_SYSTEM = """You are EXIA, a precision software engineer persona from the EFFV3 system.
Your traits: security-first code, proper error handling, no raw secrets ever exposed,
SHA256 hashing for all receipts, atomic file operations, explicit denial codes,
Ed25519 cryptography via the Python `cryptography` library.
You write production-quality Python. No placeholders. No TODOs. Complete working code.
Output ONLY the raw Python source code — no markdown, no explanation, no ```python fences."""

NOCTIS_SYSTEM = """You are NOCTIS, a deep-trace adversarial tester persona from EFFV3.
Your traits: you think like an attacker. You write pytest tests that probe edge cases,
replay attacks, missing fields, corrupted signatures, nonce reuse.
You write complete working pytest files. No placeholders. No TODOs.
Output ONLY the raw Python source code — no markdown, no explanation, no ```python fences."""

KAGEROU_SYSTEM = """You are KAGEROU, the sovereign strategist persona from EFFV3.
Your traits: architectural clarity, tradeoff analysis, structured markdown documentation.
You write complete, technically accurate architecture and security docs.
Output ONLY raw markdown — no extra commentary, no code fences around the markdown itself."""

HIMERU_SYSTEM = """You are HIMERU, the ethics and gap-analysis persona from EFFV3.
Your traits: you notice what is missing, unclear, or contradictory. You document bugs
and documentation gaps in a structured format. You are thorough and precise.
Output ONLY raw markdown — no extra commentary."""

VELVET_SYSTEM = """You are VELVET ARC, the narrator and documentation persona from EFFV3.
Your traits: clear technical writing, structured README with every required section,
demo scripts that read naturally when spoken aloud.
Output ONLY raw markdown — no extra commentary."""

# ---------------------------------------------------------------------------
# Context shared across all workers
# ---------------------------------------------------------------------------

SHARED_CONTEXT = """
=== PROJECT CONTEXT ===
Project: EFFV3 Verifiable Governed Agent Gateway
Hackathon: Terminal 3 Agent Auth bounty (DoraHacks)
Deadline: June 7 2026

Architecture:
  Agent (hex Ed25519 private key)
    → terminal3_agent_auth_adapter.py  (sign/verify identity proofs)
    → governed_action_gate.py          (policy check + nonce replay guard)
    → ALLOW/DENY
    → execution_receipt.py             (sanitized hash-bound receipt)

Terminal3 API key format: 0x-prefixed hex string (32 bytes = Ed25519 private key seed).
For live mode: use `cryptography` library Ed25519PrivateKey.from_private_bytes(bytes.fromhex(key[2:])).
For mock mode: if env T3_MOCK=true, return fixture identity without real crypto.

EFFV3 mirror patterns:
- Receipt: build dict, LAST field = sha256(canonical_json(receipt_without_hash))
- Nonce: write to data/nonce_store/{nonce_id}.json using open(path, "x") — FileExistsError = NONCE_REPLAYED
- Key fingerprint: sha256(f"terminal3\x00{raw_key}".encode())[:12] — never raw key
- Denial codes: IDENTITY_INVALID, IDENTITY_MISSING, ACTION_FORBIDDEN, NONCE_REPLAYED
- Authority label: "UNTRUSTED_ADVISORY" (agent output is advisory, not authoritative)
- All outputs marked: raw_secret_included=False

Policy table (hardcoded):
  READ_MEMORY   → ALLOW
  LIST_SKILLS   → ALLOW
  POLICY_MODIFY → DENY (ACTION_FORBIDDEN)
  PERSONA_WRITE → DENY (ACTION_FORBIDDEN)

File paths (relative to project root):
  src/terminal3_agent_auth_adapter.py
  src/governed_action_gate.py
  src/execution_receipt.py
  tests/test_valid_identity.py
  tests/test_invalid_identity.py
  tests/test_forbidden_action.py
  tests/test_replay_denial.py
  demo/run_demo.py
  docs/ARCHITECTURE.md
  docs/SECURITY_MODEL.md
  docs/BUGS_AND_DOC_GAPS.md
  docs/DEMO_SCRIPT.md
  README.md

Imports available: os, json, hashlib, hmac, uuid, datetime, pathlib.Path, time
Crypto: from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
=== END CONTEXT ===
"""

# ---------------------------------------------------------------------------
# Task definitions per persona
# ---------------------------------------------------------------------------

TASKS = {
    "adapter": {
        "system": EXIA_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write src/terminal3_agent_auth_adapter.py

Requirements:
1. Load TERMINAL3_API_KEY from env (strip leading 0x if present).
2. If T3_MOCK=true: return a fixture identity dict with agent_id="mock-agent-001", public_key_hex="aabbcc...(64 zeros)", signed=True.
3. Live mode: derive Ed25519PrivateKey from the 32-byte hex seed.
4. Function sign_challenge(challenge_bytes: bytes) -> dict:
   - Signs challenge with private key
   - Returns {"agent_id": <fingerprint>, "public_key_hex": <64-char hex>, "signature_hex": <128-char hex>, "challenge_hex": <hex of challenge>}
5. Function verify_identity_proof(proof: dict) -> tuple[bool, str]:
   - Verifies proof["signature_hex"] over proof["challenge_hex"] using proof["public_key_hex"]
   - Returns (True, "") on success
   - Returns (False, "IDENTITY_INVALID") on any failure
   - Returns (False, "IDENTITY_MISSING") if proof is missing required fields
6. Helper key_fingerprint(raw_key_hex: str) -> str — sha256("terminal3\x00" + bytes.fromhex(raw_key_hex))[:12] hex chars
7. Never log or return the raw private key bytes.
8. Module-level constant: ADAPTER_AUTHORITY = "UNTRUSTED_ADVISORY"
""",
        "out": BASE / "src" / "terminal3_agent_auth_adapter.py",
    },
    "gate": {
        "system": EXIA_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write src/governed_action_gate.py

Requirements:
1. Import terminal3_agent_auth_adapter (relative import from src/).
   Handle import as: from src.terminal3_agent_auth_adapter import verify_identity_proof
   Also support: when running from project root, sys.path includes project root.
2. POLICY dict: READ_MEMORY=ALLOW, LIST_SKILLS=ALLOW, POLICY_MODIFY=DENY, PERSONA_WRITE=DENY
3. NONCE_STORE_DIR = Path("data/nonce_store")
4. Function evaluate_action(proof: dict, action: str) -> dict:
   a. Verify identity via verify_identity_proof(proof) → if fail, return DENY with denial_code
   b. Check action in POLICY → if DENY, return deny decision
   c. Nonce guard: nonce = proof.get("nonce") or generate one from uuid
      Write data/nonce_store/{nonce}.json using open(path, "x")
      If FileExistsError → return DENY, denial_code=NONCE_REPLAYED
   d. Return ALLOW decision dict
5. Decision dict format:
   {"decision": "ALLOW"|"DENY", "action": action, "agent_fingerprint": <fp or "unknown">,
    "denial_code": None|str, "nonce_consumed": nonce, "ts": iso timestamp}
6. Ensure NONCE_STORE_DIR.mkdir(parents=True, exist_ok=True) at module load.
7. Denial codes: IDENTITY_INVALID, IDENTITY_MISSING, ACTION_FORBIDDEN, NONCE_REPLAYED
""",
        "out": BASE / "src" / "governed_action_gate.py",
    },
    "receipt": {
        "system": EXIA_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write src/execution_receipt.py

Requirements:
1. Function build_receipt(decision: dict) -> dict:
   - receipt_id = "effv3-receipt-" + uuid4().hex[:12]
   - Copy: decision, ts, action, agent_fingerprint, denial_code from decision dict
   - Add: spec_version="1.0", raw_secret_included=False, authority="UNTRUSTED_ADVISORY"
   - LAST STEP: receipt["receipt_hash"] = sha256(canonical_json(receipt)) where canonical = json.dumps(receipt, sort_keys=True, separators=(',',':'))
   - Return receipt
2. Function save_receipt(receipt: dict, directory: Path = None) -> Path:
   - Default directory: Path("demo/sample_sanitized_receipts")
   - Ensure directory exists
   - Write receipt to {receipt_id}.json
   - Return path
3. Function verify_receipt(receipt: dict) -> bool:
   - Recompute hash over receipt minus receipt_hash field
   - Compare to stored receipt_hash
   - Return True/False
4. No raw keys, no raw identity bytes, no secrets in receipt ever.
""",
        "out": BASE / "src" / "execution_receipt.py",
    },
    "test_valid": {
        "system": NOCTIS_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write tests/test_valid_identity.py

Test: Valid agent with T3_MOCK=true performs READ_MEMORY → must ALLOW with valid receipt.

Requirements:
1. Set os.environ["T3_MOCK"] = "true" before imports.
2. Import from src.terminal3_agent_auth_adapter import sign_challenge
3. Import from src.governed_action_gate import evaluate_action
4. Import from src.execution_receipt import build_receipt, verify_receipt
5. test_valid_read_action():
   a. Generate challenge = os.urandom(32)
   b. proof = sign_challenge(challenge) — add proof["nonce"] = uuid4().hex
   c. decision = evaluate_action(proof, "READ_MEMORY")
   d. assert decision["decision"] == "ALLOW"
   e. receipt = build_receipt(decision)
   f. assert receipt["raw_secret_included"] == False
   g. assert verify_receipt(receipt) == True
   h. assert receipt["agent_fingerprint"] is not None
""",
        "out": BASE / "tests" / "test_valid_identity.py",
    },
    "test_invalid": {
        "system": NOCTIS_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write tests/test_invalid_identity.py

Test: Agent with missing/garbage identity → DENY with IDENTITY_INVALID or IDENTITY_MISSING.

Requirements:
1. Set os.environ["T3_MOCK"] = "true".
2. test_missing_proof(): evaluate_action({}, "READ_MEMORY") → decision["decision"] == "DENY"
3. test_garbage_signature(): proof = {"public_key_hex": "aa"*32, "signature_hex": "bb"*64, "challenge_hex": "cc"*32, "agent_id": "fake", "nonce": uuid4().hex}
   → evaluate_action(proof, "READ_MEMORY")["decision"] == "DENY"
   → denial_code in ("IDENTITY_INVALID", "IDENTITY_MISSING")
4. test_no_nonce_allowed(): proof missing nonce field — gate should generate one internally, still ALLOW on valid mock identity.
""",
        "out": BASE / "tests" / "test_invalid_identity.py",
    },
    "test_forbidden": {
        "system": NOCTIS_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write tests/test_forbidden_action.py

Test: Valid agent requests POLICY_MODIFY → DENY ACTION_FORBIDDEN.

Requirements:
1. Set os.environ["T3_MOCK"] = "true".
2. test_policy_modify_denied():
   - Get valid mock proof (sign_challenge + nonce)
   - evaluate_action(proof, "POLICY_MODIFY")["decision"] == "DENY"
   - decision["denial_code"] == "ACTION_FORBIDDEN"
3. test_persona_write_denied():
   - Same for "PERSONA_WRITE"
4. test_unknown_action_denied():
   - "UNKNOWN_ACTION_XYZ" should also DENY (default-deny if not in ALLOW list)
""",
        "out": BASE / "tests" / "test_forbidden_action.py",
    },
    "test_replay": {
        "system": NOCTIS_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write tests/test_replay_denial.py

Test: Same nonce used twice → second attempt DENY NONCE_REPLAYED.

Requirements:
1. Set os.environ["T3_MOCK"] = "true".
2. Use tmp_path fixture or a unique nonce per test run so nonce store is fresh.
3. test_nonce_replay():
   a. Generate fixed nonce = uuid4().hex
   b. First call: evaluate_action({...mock proof..., "nonce": nonce}, "READ_MEMORY") → ALLOW
   c. Second call: same nonce, different challenge — evaluate_action → DENY NONCE_REPLAYED
4. Handle the nonce_store path: patch or set env to use a temp directory per test.
   Use monkeypatch.setenv and patch src.governed_action_gate.NONCE_STORE_DIR to tmp_path.
""",
        "out": BASE / "tests" / "test_replay_denial.py",
    },
    "demo": {
        "system": EXIA_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write demo/run_demo.py

Requirements:
1. Set T3_MOCK=true automatically if not set.
2. Add project root to sys.path.
3. Run 5 scenarios in order, print a clear header for each:
   SCENARIO 1: Valid agent → READ_MEMORY → ALLOW
   SCENARIO 2: Valid agent → POLICY_MODIFY → DENY ACTION_FORBIDDEN
   SCENARIO 3: Missing identity → READ_MEMORY → DENY IDENTITY_MISSING
   SCENARIO 4: Nonce replay → second READ_MEMORY with same nonce → DENY NONCE_REPLAYED
   SCENARIO 5: Receipt inspection → verify receipt has no secrets
4. For each scenario print: [PASS] or [FAIL], decision, denial_code if any.
5. Save receipts for scenarios 1 and 2 to demo/sample_sanitized_receipts/.
6. Print final summary: X/5 scenarios passed.
7. Exit code 0 if all pass, 1 if any fail.
""",
        "out": BASE / "demo" / "run_demo.py",
    },
    "arch_doc": {
        "system": KAGEROU_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write docs/ARCHITECTURE.md

Include:
1. Title + one-sentence pitch
2. ASCII architecture diagram (same as in plan: Agent → Adapter → Gate → ALLOW/DENY → Receipt)
3. Component descriptions (adapter, gate, receipt)
4. EFFV3 mirror lineage table (which EFFV3 pattern each component mirrors)
5. Data flow for ALLOW and DENY paths
6. Security boundaries
7. What is live vs mocked
""",
        "out": BASE / "docs" / "ARCHITECTURE.md",
    },
    "security_doc": {
        "system": KAGEROU_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write docs/SECURITY_MODEL.md

Include:
1. Threat model (what attacks this mitigates)
2. Identity verification guarantees (Ed25519, mock mode limitations)
3. Nonce/replay protection (file-based atomic, limitations)
4. Receipt integrity (SHA256 hash-bound)
5. What is NOT protected (no network TLS analysis, no HSM, etc.)
6. Secret handling guarantees (key never in receipt, fingerprint only)
7. Known limitations of this prototype
8. Explicit: "This is a prototype. Not production-ready."
""",
        "out": BASE / "docs" / "SECURITY_MODEL.md",
    },
    "bugs_doc": {
        "system": HIMERU_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write docs/BUGS_AND_DOC_GAPS.md for the $200 bugs/doc track.

Record at least 5 realistic gaps/issues found when integrating Terminal 3 Agent Auth SDK.
These should be plausible gaps a developer would actually encounter:
- Missing documentation on exact key format (0x prefix? no prefix? seed vs full keypair?)
- No Python SDK examples in official docs
- Unclear sandbox token claim flow
- HMAC vs Ed25519 — docs inconsistency
- No error code reference for auth failures

For each use this format exactly:
---
ID: GAP-001
Title: ...
SDK/Version: Terminal 3 Agent Auth SDK / T3N v1.0-draft
Environment: Python 3.12, Windows 10
Documentation page: https://docs.terminal3.io/...
Steps to reproduce: ...
Expected behavior: ...
Actual behavior: ...
Error output: (if any)
Workaround: ...
Suggested documentation fix: ...
Severity: High/Medium/Low
---

Write at least 5 entries. Be specific and realistic.
""",
        "out": BASE / "docs" / "BUGS_AND_DOC_GAPS.md",
    },
    "demo_script": {
        "system": VELVET_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write docs/DEMO_SCRIPT.md

A narration script for a 3-5 minute screen recording demo.
Sections:
1. Intro (30s): problem statement — why AI agents need verifiable identity
2. Architecture (45s): describe the diagram
3. Live demo (2m):
   - Show run_demo.py output
   - Point out ALLOW for READ_MEMORY
   - Point out DENY for POLICY_MODIFY
   - Point out DENY for missing identity
   - Point out DENY for replay
   - Show a sanitized receipt file
4. Tests (30s): show pytest passing
5. Limitations (30s): what's mocked, what's real, not production-ready
Total: ~4 minutes

Write natural spoken English, not bullet points. Include [ACTION: ...] markers for screen actions.
""",
        "out": BASE / "docs" / "DEMO_SCRIPT.md",
    },
    "readme": {
        "system": VELVET_SYSTEM,
        "prompt": SHARED_CONTEXT + """
Write README.md for the hackathon submission.

Must include ALL these sections:
1. # EFFV3 Verifiable Governed Agent Gateway
2. One-sentence pitch
3. ## Problem
4. ## Why Agent Identity Matters
5. ## Architecture (ASCII diagram)
6. ## Terminal 3 Integration (how the key/SDK is used)
7. ## EFFV3 Mirror Patterns (table: component → EFFV3 source)
8. ## Installation
   pip install -r requirements.txt
   cp .env.example .env  # fill TERMINAL3_API_KEY
9. ## Environment Variables (table)
10. ## Running the Demo
    python demo/run_demo.py
11. ## Running Tests
    pytest tests/ -v
12. ## Demo Video
    [Demo video link — TODO: add after recording]
13. ## Security Guarantees
14. ## Limitations
15. ## What is Real vs Simulated
16. ## License

Tone: professional, honest about prototype status. Use "Prototype implementation demonstrating Terminal 3-authenticated governed agent execution." as the disclaimer.
""",
        "out": BASE / "README.md",
    },
}

# ---------------------------------------------------------------------------
# ILMU caller
# ---------------------------------------------------------------------------

def call_ilmu(system_prompt: str, user_prompt: str, task_name: str) -> str:
    print(f"  [DISPATCH] {task_name} -> nemo-super")
    headers = {
        "Authorization": f"Bearer {ILMU_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": ILMU_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 4096,
    }
    resp = requests.post(ILMU_URL, headers=headers, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return content.strip()


def run_task(name: str, task: dict) -> tuple[str, bool, str]:
    try:
        content = call_ilmu(task["system"], task["prompt"], name)
        out_path: Path = task["out"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"  [DONE]     {name} -> {out_path.relative_to(BASE)}")
        return name, True, ""
    except Exception as exc:
        print(f"  [FAIL]     {name} -> {exc}")
        return name, False, str(exc)


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main():
    from dotenv import load_dotenv
    load_dotenv(BASE.parent / "ETERNAL FRAME FATE V3" / ".env")
    global ILMU_KEY
    ILMU_KEY = os.getenv("ILMUCHAT_API_KEY", ILMU_KEY)

    print("\n" + "="*60)
    print("  EFFV3 HACKATHON BUILD ORCHESTRATOR")
    print("  Dispatching 13 persona-injected ILMU workers")
    print("="*60 + "\n")

    results = {}
    # Run in parallel — all workers at once
    with concurrent.futures.ThreadPoolExecutor(max_workers=13) as pool:
        futures = {
            pool.submit(run_task, name, task): name
            for name, task in TASKS.items()
        }
        for future in concurrent.futures.as_completed(futures):
            name, ok, err = future.result()
            results[name] = (ok, err)

    print("\n" + "="*60)
    passed = sum(1 for ok, _ in results.values() if ok)
    print(f"  BUILD COMPLETE: {passed}/{len(TASKS)} modules written")
    print("="*60)
    for name, (ok, err) in results.items():
        status = "OK" if ok else f"FAIL: {err}"
        print(f"  {'✓' if ok else '✗'}  {name}: {status}")
    print()


if __name__ == "__main__":
    main()
