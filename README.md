# EFFV3 — Verifiable Governed Agent Gateway

> Prototype: Terminal 3-authenticated governed agent execution with cryptographic identity, policy enforcement, and tamper-proof receipts.

**Demo Video:** https://youtu.be/u6JjDT3Uizc

---

## Reviewer Quick Pointer

If you are reviewing the **Terminal 3 / T3 SDK-auth path**, start here:

- `src/terminal3_agent_auth_adapter.py`
  Loads `TERMINAL3_API_KEY`, derives the Ed25519 key, signs the action proof, and verifies the proof.
- `src/governed_action_gate.py`
  Consumes the verified proof, applies policy, and blocks nonce replay.
- `tests/test_valid_identity.py`
  Shows the valid signed-proof path.
- `tests/test_replay_denial.py`
  Shows replay protection on the same nonce.
- `demo/run_demo.py`
  Runs the end-to-end governed flow and emits sanitized receipts.
- `docs/REVIEWER_GUIDE.md`
  One-page map of the exact auth, gate, test, and demo files to review.

Important scope note:
- This repo contains the **implemented auth adapter and governed execution flow**.
- It does **not** claim a full hosted Terminal 3 backend or attestation service.
- The real implemented piece is the local cryptographic proof flow around the Terminal 3 API key.

---

## The Problem

AI agents have no identity. Nothing stops a fake agent from impersonating a real one, replaying old requests, or acting without an audit trail.

This prototype fixes three things:
- **Who are you?** — Ed25519 identity proof bound to Terminal 3 API key
- **Are you allowed?** — Policy gate that blocks forbidden actions
- **What did you do?** — Hash-bound receipt with no secrets exposed

---

## How It Works

```
Agent (Ed25519 key)
        │
        ▼
terminal3_agent_auth_adapter.py   ← proves identity via Terminal 3 API key
        │
        ▼
governed_action_gate.py           ← checks policy + blocks replay attacks
        │
        ▼
execution_receipt.py              ← issues hash-bound receipt (no secrets)
        │
        ▼
ALLOW  or  DENY (IDENTITY_INVALID | ACTION_FORBIDDEN | NONCE_REPLAYED)
```

---

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env        # add your TERMINAL3_API_KEY
python demo/run_demo.py     # run all 5 scenarios
pytest tests/ -v            # run all 12 tests
```

### Environment Variables

| Variable | What it does | Example |
|---|---|---|
| `TERMINAL3_API_KEY` | 0x-prefixed hex string — 32-byte Ed25519 seed | `0xa1b2c3...ef` (64 hex chars) |
| `T3_MOCK` | Skip real crypto for local dev | `true` / `false` |

---

## Terminal 3 Integration

| Topic | Detail |
|---|---|
| Key format | `0x` + 64 hex chars (32-byte Ed25519 private key seed) |
| Live mode | `Ed25519PrivateKey.from_private_bytes(bytes.fromhex(key[2:]))` |
| Mock mode | Returns fixture identity — no real crypto, no network call |
| Fingerprint | `sha256(b"terminal3\x00" + pub_key_bytes)[:12]` — public key only, never raw seed |
| Key exposure | Never — only 12-byte fingerprint used in logs and receipts |

---

## Security Guarantees

| Property | How |
|---|---|
| Cryptographic identity | Ed25519 signature over action + nonce + audience |
| Replay protection | Atomic nonce file — `open(path, "x")` raises `FileExistsError` on reuse |
| Policy enforcement | Allowlist — `POLICY_MODIFY`, `PERSONA_WRITE` always denied |
| Tamper-proof receipts | `sha256(canonical_json)` as last field — any mutation breaks hash |
| No secret leakage | `raw_secret_included=False` on every output |
| Advisory authority | `UNTRUSTED_ADVISORY` label — agent output never treated as authoritative |

---

## What Is Real vs Mocked

| Component | Status |
|---|---|
| Ed25519 key derivation + signing | **Real** (`cryptography` library) |
| Nonce store atomic file lock | **Real** (filesystem `x`-mode) |
| sha256 hash-bound receipts | **Real** |
| Policy enforcement | **Real** |
| Terminal 3 live API endpoint | **Mocked** (`T3_MOCK=true` in demo) |
| Live network attestation | **Mocked** |
| Distributed nonce coordination | **Not implemented** |

---

## Test Coverage (12/12)

| Test file | What it proves |
|---|---|
| `test_valid_identity.py` | Valid agent gets ALLOW + clean receipt |
| `test_forbidden_action.py` | POLICY_MODIFY, PERSONA_WRITE, unknown actions all denied |
| `test_invalid_identity.py` | Missing proof, garbage signature, missing nonce all denied |
| `test_replay_denial.py` | Same nonce twice = NONCE_REPLAYED |
| `test_receipt_integrity.py` | Tamper detection, deny receipt has no secrets, fingerprint safety |

---

## Known Limitations

- Hardcoded policy table — no dynamic updates
- Nonce store is local filesystem — not distributed or horizontally scalable
- Policy gate is local — root of trust depends on host integrity, no decentralized layer
- No key rotation or revocation mechanism
- No KMS or external secret management
- Async agent workflows not covered

---

## Doc Gaps Filed

5 gaps reported in [`docs/BUGS_AND_DOC_GAPS.md`](docs/BUGS_AND_DOC_GAPS.md):
API key format ambiguity · missing Python SDK examples · mock mode behavior · HMAC vs Ed25519 inconsistency · undocumented error codes

---

## License

MIT — see [LICENSE](LICENSE)
