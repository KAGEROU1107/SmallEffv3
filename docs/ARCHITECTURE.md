# Architecture — EFFV3 Verifiable Governed Agent Gateway

A lightweight, policy-enforced adapter that cryptographically verifies agent identity and enforces governance rules before any action executes.

---

## Flow Diagram

```
Agent (Ed25519 key)
        │
        ▼
terminal3_agent_auth_adapter.py   [sign / verify identity proof]
        │
        ▼
governed_action_gate.py           [policy check + nonce replay guard]
        │
        ├── ALLOW ──▶ execution_receipt.py [hash-bound receipt]
        │
        └── DENY  ──▶ denial code returned
                      (IDENTITY_INVALID | IDENTITY_MISSING | ACTION_FORBIDDEN | NONCE_REPLAYED)
```

---

## Components

### terminal3_agent_auth_adapter.py

Handles cryptographic identity verification using the Terminal 3 API key.

| Mode | Behavior |
|---|---|
| **Live** (`T3_MOCK=false`) | Derives Ed25519 private key from `0x`-prefixed hex seed, signs and verifies proofs |
| **Mock** (`T3_MOCK=true`) | Returns fixture identity — no real cryptography |

- Key fingerprint: `sha256(b"terminal3\x00" + pub_key_bytes)[:12]` — public key only, never raw seed
- Raw key never leaves this component

---

### governed_action_gate.py

Enforces governance policy and replay protection.

**Policy table:**

| Action | Decision |
|---|---|
| `READ_MEMORY` | ALLOW |
| `LIST_SKILLS` | ALLOW |
| `POLICY_MODIFY` | DENY (`ACTION_FORBIDDEN`) |
| `PERSONA_WRITE` | DENY (`ACTION_FORBIDDEN`) |
| anything else | DENY (`ACTION_FORBIDDEN`) |

**Replay guard:** writes nonce to `data/nonce_store/{nonce_id}.json` using `open(path, "x")`.
`FileExistsError` → `NONCE_REPLAYED`.

---

### execution_receipt.py

Generates sanitized, hash-bound receipts for every decision.

- Builds receipt dict: action, agent fingerprint, timestamp, nonce hash, decision
- Last field = `sha256(canonical_json(receipt_without_hash))`
- All outputs marked `raw_secret_included=False`
- Receipts generated for both ALLOW and DENY decisions

---

## Data Flow

### ALLOW Path

```
1. Agent provides TERMINAL3_API_KEY (0x-prefixed hex)
2. adapter → verifies identity → returns agent fingerprint
3. gate → checks policy → records nonce via open("x")
4. receipt → builds dict → computes sha256 hash → outputs receipt
5. Action proceeds
```

### DENY Path

```
1. Invalid/missing key → IDENTITY_INVALID or IDENTITY_MISSING
   OR
2. Valid key + forbidden action → ACTION_FORBIDDEN
   OR
3. Valid key + allowed action + reused nonce → NONCE_REPLAYED

→ Denial returned immediately, no receipt generated for identity failures
```

---

## Security Boundaries

| Boundary | Mechanism |
|---|---|
| Cryptographic | Private key exists only inside adapter; never crosses component boundary |
| Identity | Raw keys never shared — only 12-byte fingerprint used across components |
| State | Nonce store is append-only via `open("x")` — replay prevented at filesystem level |
| Execution | Receipts contain no secrets — `raw_secret_included=False` enforced |
| Policy | Deny list hardcoded — cannot be bypassed without code change |

---

## Live vs Mock Behavior

| Aspect | Live Mode | Mock Mode |
|---|---|---|
| Identity | Real Ed25519 from `0x`-prefixed hex seed | Fixed fixture identity |
| Crypto | `cryptography` library — sign + verify | No cryptography — static proof |
| Nonce store | Real filesystem writes | Real filesystem writes (replay guard still active) |
| Receipts | Hash-bound, agent-attributable | Hash-bound, mock identity |
| Use case | Production / integration testing | Unit tests, CI/CD, local dev |

---

## EFFV3 Mirror Patterns

| Pattern | Component | Implementation |
|---|---|---|
| Receipt LAST field = `sha256(canonical_json)` | `execution_receipt.py` | Receipt generation |
| Nonce: `open(path, "x")` → `FileExistsError` = replay | `governed_action_gate.py` | Replay guard |
| Fingerprint: `sha256(b"terminal3\x00" + pub_key_bytes)[:12]` | `terminal3_agent_auth_adapter.py` | Identity protection |
| Denial codes: `IDENTITY_INVALID`, `IDENTITY_MISSING`, `ACTION_FORBIDDEN`, `NONCE_REPLAYED` | `governed_action_gate.py` | Error handling |
| Authority label: `UNTRUSTED_ADVISORY` | `execution_receipt.py` | Receipt metadata |
| `raw_secret_included=False` | `execution_receipt.py` | All receipt outputs |
