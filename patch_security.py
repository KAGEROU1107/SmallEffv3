"""
Security patch orchestrator — Boss dispatches, ILMU patches.
Fixes 6 issues from security audit.
"""
import os, sys, json, requests, concurrent.futures
from pathlib import Path

ILMU_URL = "https://api.ilmu.ai/v1/chat/completions"
ILMU_KEY = os.getenv("ILMUCHAT_API_KEY", "")
ILMU_MODEL = "nemo-super"
TIMEOUT = 300
BASE = Path(__file__).parent

EXIA = """You are EXIA, precision security engineer from EFFV3.
Security-first. No shortcuts. No TODOs. Complete working Python.
Output ONLY raw Python — no markdown fences, no explanation."""

NOCTIS = """You are NOCTIS, adversarial tester from EFFV3.
You write pytest tests that probe edge cases and security boundaries.
Output ONLY raw Python — no markdown fences, no explanation."""

HIMERU = """You are HIMERU, gap-analysis persona from EFFV3.
You write honest documentation about what is verified vs assumed.
Output ONLY raw markdown."""

CURRENT_ADAPTER = (BASE / "src/terminal3_agent_auth_adapter.py").read_text()
CURRENT_GATE = (BASE / "src/governed_action_gate.py").read_text()
CURRENT_RECEIPT = (BASE / "src/execution_receipt.py").read_text()
CURRENT_BUGS = (BASE / "docs/BUGS_AND_DOC_GAPS.md").read_text()
CURRENT_TEST_VALID = (BASE / "tests/test_valid_identity.py").read_text()
CURRENT_TEST_INVALID = (BASE / "tests/test_invalid_identity.py").read_text()
CURRENT_TEST_FORBIDDEN = (BASE / "tests/test_forbidden_action.py").read_text()
CURRENT_TEST_REPLAY = (BASE / "tests/test_replay_denial.py").read_text()
CURRENT_DEMO = (BASE / "demo/run_demo.py").read_text()

PATCHES = {
    "adapter": {
        "system": EXIA,
        "prompt": f"""Rewrite src/terminal3_agent_auth_adapter.py applying these security fixes:

FIX 1 — Bind signature to action+nonce+audience (critical):
Replace sign_challenge(challenge_bytes) with sign_action_request(action: str, nonce: str) -> dict
The signed payload must be a canonical JSON dict containing:
  agent_id, public_key_hex, action, nonce, issued_at, expires_at (now+300s), audience="small-effv3-gate"
Compute payload_hash = sha256(canonical_json(payload))
Sign payload_hash.encode() with Ed25519 private key.
Return the payload dict plus payload_hash and signature_hex.

FIX 2 — agent_id must equal fingerprint(public_key):
In verify_action_request(proof, expected_action) -> tuple[bool, str]:
- Check required fields: agent_id, public_key_hex, action, nonce, issued_at, expires_at, audience, signature_hex, payload_hash
- Return (False, "IDENTITY_MISSING") if any missing
- Check proof["action"] == expected_action else (False, "IDENTITY_INVALID")
- Check proof["audience"] == "small-effv3-gate" else (False, "IDENTITY_INVALID")
- Check expiry: parse expires_at, if now > expires return (False, "PROOF_EXPIRED")
- Recompute payload_hash from fields excluding signature_hex — if mismatch (False, "IDENTITY_INVALID")
- In mock mode (T3_MOCK=true): return (True, "") after structural checks above
- In live mode: verify agent_id == key_fingerprint(public_key_hex), else (False, "IDENTITY_INVALID")
- In live mode: verify Ed25519 signature over payload_hash.encode()

Keep: ADAPTER_AUTHORITY, AUDIENCE, key_fingerprint helper, _canonical, _sha256, _is_mock, _load_private_key.
Mock mode: sign_action_request returns fixture with correct structure (not random bytes).

Current file:
{CURRENT_ADAPTER}""",
        "out": BASE / "src/terminal3_agent_auth_adapter.py",
    },
    "gate": {
        "system": EXIA,
        "prompt": f"""Rewrite src/governed_action_gate.py applying these security fixes:

FIX 3 — Missing nonce -> DENY NONCE_MISSING (do NOT auto-generate):
If proof.get("nonce") is falsy, return DENY with denial_code="NONCE_MISSING" immediately.

FIX 4 — Nonce path traversal prevention:
Filename = hashlib.sha256(nonce.encode()).hexdigest() + ".json"
NEVER use the raw nonce string in a filesystem path.

FIX 5 — Receipt completeness:
Add to every decision dict: nonce_hash (sha256(nonce)), proof_hash (sha256(canonical_json(proof))), policy_version="1.0"

Also update to call verify_action_request(proof, action) instead of verify_identity_proof(proof).

Import: from src.terminal3_agent_auth_adapter import verify_action_request

Keep all existing denial codes. Add NONCE_MISSING. Default-deny any action not in POLICY.

Current file:
{CURRENT_GATE}""",
        "out": BASE / "src/governed_action_gate.py",
    },
    "receipt": {
        "system": EXIA,
        "prompt": f"""Rewrite src/execution_receipt.py applying these fixes:

FIX 5 — Receipt must include nonce_hash, proof_hash, policy_version from decision dict.

FIX 6 — Actual secret scanning before save:
Add _scan_for_secrets(data: str) -> bool that checks for:
  - "TERMINAL3_API_KEY", "ILMUCHAT_API_KEY", "sk-", "sk-or-", "0xdd99"
  - Also first 8 chars of os.getenv("TERMINAL3_API_KEY","") if set and len>8
In save_receipt(): call _scan_for_secrets on serialized receipt.
If found: raise ValueError("SECRET_EXPOSURE_DETECTED: save aborted")

receipt["receipt_hash"] must still be computed LAST over all other fields.

Current file:
{CURRENT_RECEIPT}""",
        "out": BASE / "src/execution_receipt.py",
    },
    "tests": {
        "system": NOCTIS,
        "prompt": f"""Rewrite all 4 test files. The adapter API changed:
- sign_challenge(challenge_bytes) is now sign_action_request(action: str, nonce: str) -> dict
- verify_identity_proof is now verify_action_request(proof, action)
- Missing nonce now -> DENY NONCE_MISSING (not ALLOW)
- The proof dict now contains: agent_id, public_key_hex, action, nonce, issued_at, expires_at, audience, payload_hash, signature_hex

All tests use T3_MOCK=true. Set os.environ["T3_MOCK"]="true" at top of each file.

Write 4 complete test files separated by === FILE: tests/test_NAME.py === headers:

=== FILE: tests/test_valid_identity.py ===
test_valid_read_action(): sign_action_request("READ_MEMORY", uuid4().hex) -> evaluate_action(proof, "READ_MEMORY") -> ALLOW -> build_receipt -> verify_receipt == True, raw_secret_included==False

=== FILE: tests/test_invalid_identity.py ===
test_missing_proof(): evaluate_action({{}}, "READ_MEMORY") -> DENY
test_garbage_signature(monkeypatch): monkeypatch.setenv("T3_MOCK","false"), build a proof with correct structure but garbage signature_hex/public_key_hex -> DENY IDENTITY_INVALID or IDENTITY_MISSING
test_missing_nonce(): valid mock proof but no nonce field -> DENY NONCE_MISSING

=== FILE: tests/test_forbidden_action.py ===
test_policy_modify_denied(): sign_action_request("POLICY_MODIFY", uuid4().hex) -> evaluate_action -> DENY ACTION_FORBIDDEN
test_persona_write_denied(): same for PERSONA_WRITE
test_unknown_action_denied(): same for "UNKNOWN_ACTION_XYZ"

=== FILE: tests/test_replay_denial.py ===
test_nonce_replay(tmp_path, monkeypatch): patch NONCE_STORE_DIR to tmp_path
  nonce=uuid4().hex
  proof1=sign_action_request("READ_MEMORY", nonce) -> evaluate_action -> ALLOW
  proof2=sign_action_request("LIST_SKILLS", nonce) -> evaluate_action("LIST_SKILLS") -> DENY NONCE_REPLAYED

Note for replay test: the same nonce is used in two different proofs for two different actions.
The second call must pass the action matching the proof (proof2 was signed for LIST_SKILLS).

Current tests for reference:
{CURRENT_TEST_VALID}
{CURRENT_TEST_INVALID}
{CURRENT_TEST_FORBIDDEN}
{CURRENT_TEST_REPLAY}""",
        "out": None,  # multiple files — handled specially
    },
    "demo": {
        "system": EXIA,
        "prompt": f"""Rewrite demo/run_demo.py to use the new API:
- import sign_action_request (not sign_challenge)
- Each scenario must generate a nonce = uuid4().hex and call sign_action_request(action, nonce)
- Then call evaluate_action(proof, action)
- Scenario 3 (missing identity): pass {{}} directly to evaluate_action
- Scenario 4 (nonce replay): use same nonce for two different sign_action_request calls
- All 5 scenarios, same structure as before

Current demo:
{CURRENT_DEMO}""",
        "out": BASE / "demo/run_demo.py",
    },
    "bugs_doc": {
        "system": HIMERU,
        "prompt": f"""Rewrite docs/BUGS_AND_DOC_GAPS.md.

IMPORTANT: This file must be HONEST. Only report gaps that are genuinely observed or clearly inferred from Terminal 3 documentation. Do NOT describe our own invented adapter conventions as Terminal 3 SDK behavior.

Add a clear header section:
## Disclaimer
These gaps were identified while building a prototype that ASSUMES Terminal 3 uses Ed25519 keys based on the 0x-prefixed hex key format. The actual Terminal 3 SDK integration is pending. Gaps marked [ASSUMED] are based on reasonable inference; gaps marked [VERIFIED] were reproduced against actual documentation.

Then rewrite each entry. For entries that described our own code's assumptions (Ed25519 format, denial codes, etc.) — relabel them as [ASSUMED] gaps about what the Terminal 3 documentation SHOULD clarify.

Keep the structured format:
---
ID: GAP-XXX
Status: [ASSUMED] or [VERIFIED]
Title: ...
...
---

Current file:
{CURRENT_BUGS}""",
        "out": BASE / "docs/BUGS_AND_DOC_GAPS.md",
    },
}


def call_ilmu(system: str, prompt: str, name: str) -> str:
    print(f"  [DISPATCH] {name} -> nemo-super")
    r = requests.post(ILMU_URL, headers={
        "Authorization": f"Bearer {ILMU_KEY}",
        "Content-Type": "application/json",
    }, json={
        "model": ILMU_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "max_tokens": 4096,
    }, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def run_task(name, task):
    try:
        content = call_ilmu(task["system"], task["prompt"], name)

        if name == "tests":
            # Split multi-file output
            import re
            parts = re.split(r'=== FILE: (tests/\S+) ===', content)
            # parts[0] = preamble, then [filename, content, filename, content, ...]
            i = 1
            while i < len(parts) - 1:
                fname = parts[i].strip()
                fdata = parts[i+1].strip()
                out = BASE / fname
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(fdata, encoding="utf-8")
                print(f"  [DONE]     {fname}")
                i += 2
        else:
            out = task["out"]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding="utf-8")
            print(f"  [DONE]     {out.relative_to(BASE)}")

        return name, True, ""
    except Exception as exc:
        print(f"  [FAIL]     {name} -> {exc}")
        return name, False, str(exc)


def main():
    from dotenv import load_dotenv
    load_dotenv(BASE.parent / "ETERNAL FRAME FATE V3" / ".env")
    global ILMU_KEY
    ILMU_KEY = os.getenv("ILMUCHAT_API_KEY", ILMU_KEY)

    print("\n" + "="*60)
    print("  SECURITY PATCH — 6 fixes, ILMU workers dispatched")
    print("="*60 + "\n")

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(run_task, name, task): name for name, task in PATCHES.items()}
        for f in concurrent.futures.as_completed(futures):
            name, ok, err = f.result()
            results[name] = (ok, err)

    print("\n" + "="*60)
    passed = sum(1 for ok, _ in results.values() if ok)
    print(f"  PATCH COMPLETE: {passed}/{len(PATCHES)} modules patched")
    print("="*60)
    for name, (ok, err) in results.items():
        print(f"  {'OK' if ok else 'FAIL'}  {name}" + (f": {err}" if not ok else ""))
    print()


if __name__ == "__main__":
    main()
