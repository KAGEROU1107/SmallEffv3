# EFFV3 Verifiable Governed Agent Gateway
A lightweight, policy-enforced adapter that cryptographically verifies agent identity and enforces governance rules before action execution.

## ASCII Architecture Diagram
```
Agent (Ed25519 key)
        ↓
terminal3_agent_auth_adapter.py  [sign/verify identity proof]
        ↓
governed_action_gate.py          [policy check + nonce replay guard]
        ↓
    ┌─────────────┐
    │   ALLOW     │ ←── execution_receipt.py [hash-bound receipt]
    │             │
DENY  └─────────────┘  (denial codes: IDENTITY_INVALID, IDENTITY_MISSING, ACTION_FORBIDDEN, NONCE_REPLAYED)
```

## Component Descriptions

### terminal3_agent_auth_adapter.py
Handles cryptographic identity verification using Terminal3 API key format.  
- In **live mode**: Derives Ed25519 private key from `0x`-prefixed hex seed, signs challenges, verifies proofs.  
- In **mock mode** (`T3_MOCK=true`): Returns fixture identity without real cryptography.  
- Outputs: Verified agent identity or denial (`IDENTITY_INVALID`, `IDENTITY_MISSING`).  
- Never exposes raw keys; uses key fingerprint: `sha256(f"terminal3\x00{raw_key}".encode())[:12]`.

### governed_action_gate.py
Enforces governance policy and replay protection.  
- Checks action against hardcoded policy table:  
  - `READ_MEMORY` → ALLOW  
  - `LIST_SKILLS` → ALLOW  
  - `POLICY_MODIFY` → DENY (`ACTION_FORBIDDEN`)  
  - `PERSONA_WRITE` → DENY (`ACTION_FORBIDDEN`)  
- Implements nonce replay guard: writes nonce to `data/nonce_store/{nonce_id}.json` using `open(path, "x")`; `FileExistsError` → `NONCE_REPLAYED`.  
- Outputs: `ALLOW` or denial reason.

### execution_receipt.py
Generates sanitized, hash-bound receipts for allowed actions.  
- Builds receipt dict from action, identity fingerprint, timestamp, and nonce.  
- Computes `LAST` field as `sha256(canonical_json(receipt_without_hash))`.  
- Marks all outputs with `raw_secret_included=False`.  
- Output: JSON-serializable receipt dict ready for logging or transmission.

## EFFV3 Mirror Lineage Table

| EFFV3 Pattern                  | Component                            | Mirrored In                          |
|--------------------------------|--------------------------------------|--------------------------------------|
| Receipt: LAST = hash(canonical_json without hash) | execution_receipt.py | Receipt generation                   |
| Nonce store: open(path, "x") → FileExistsError = replay | governed_action_gate.py | 第四章: Nonce Replay Guard           |
| Key fingerprint: sha256(prefix + raw_key)[:12] | terminal3_agent_auth_adapter.py | Identity protection                  |
| Denial codes: IDENTITY_INVALID, etc. | governed_action_gate.py | Error handling                       |
| Authority label: UNTRUSTED_ADVISORY | execution_receipt.py | Receipt metadata (implied)           |
| raw_secret_included=False      | execution_receipt.py                 | All receipt outputs                  |

## Data Flow

### ALLOW Path
1. Agent provides Terminal3 API key (`0x...`)  
2. `adapter`: Verifies identity (live/mock) → returns agent fingerprint  
3. `gate`: Checks policy → if ALLOWED, records nonce via `open("x")`  
4. `receipt`: Builds dict → computes `LAST` hash → outputs signed receipt  
5. System proceeds with action; receipt stored/transmitted  

### DENY Path
1. Agent provides invalid/missing key → `adapter` → `IDENTITY_INVALID`/`IDENTITY_MISSING`  
   OR  
2. Valid key but forbidden action → `gate` → `ACTION_FORBIDDEN`  
   OR  
3. Valid key + allowed action but reused nonce → `gate` → `NONCE_REPLAYED`  
4. Denial returned immediately; no receipt generated  

## Security Boundaries
- **Cryptographic Boundary**: Private key material only exists in `adapter` (live mode) or is mocked; never leaves component.  
- **Identity Boundary**: Raw keys never exposed; only fingerprints (`sha256(... )[:12]`) shared across components.  
- **State Boundary**: Nonce store (`data/nonce_store/`) is append-only via `open("x")`; replay prevented at filesystem level.  
- **Execution Boundary**: `receipt` outputs contain no secrets; `raw_secret_included=False` enforced.  
- **Policy Boundary**: Hardcoded deny list (`POLICY_MODIFY`, `PERSONA_WRITE`) cannot be bypassed without code change.  

## Live vs Mocked Behavior
| Aspect          | Live Mode (`T3_MOCK` unset/false)                     | Mock Mode (`T3_MOCK=true`)                          |
|-----------------|-------------------------------------------------------|-----------------------------------------------------|
| Identity        | Real Ed25519 key from `0x`-prefixed hex seed          | Fixture identity (fixed fingerprint)                |
| Crypto          | Uses `cryptography` library for sign/verify           | No cryptography; returns static proof               |
| Nonce Store     | Real filesystem writes to `data/nonce_store/`         | Same real writes (replay guard still active)        |
| Receipts        | Hash-bound, agent-attributable                        | Hash-bound, but identity is mock (testing-safe)     |
| Use Case        | Production, integration testing                       | Unit tests, CI/CD, local dev without keys           |