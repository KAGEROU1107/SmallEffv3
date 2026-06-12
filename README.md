# SmallEffv3 — AI Agent Authorization Gateway

> **Terminal 3 Agent Dev Kit Bounty Submission**
> Real T3N testnet integration — `@terminal3/t3n-sdk` npm package, no local mock crypto.

---

## The Problem

AI agents have no verifiable identity. Nothing prevents a rogue or compromised agent from:
- **Impersonating** a legitimate agent (no cryptographic identity)
- **Replaying** old requests (no per-call nonce)
- **Exceeding scope** (no function-level authorization)
- **Operating indefinitely** after compromise (no instant revocation)

Every enterprise deploying AI agents faces this. The attack surface grows with every autonomous agent added to the system.

## The Solution

SmallEffv3 is a **governed authorization gateway** that every AI agent must pass through before executing a sensitive action. It uses Terminal 3's Agent Auth SDK to enforce:

| Guarantee | How |
|---|---|
| Cryptographic identity | Real `DelegationCredential` from T3N SDK — `buildDelegationCredential()` + `signCredential()` |
| Time-bounded access | `not_before_secs` / `not_after_secs` checked inside the TEE (not by the caller) |
| Scope enforcement | `functions[]` allowlist in the credential — TEE rejects out-of-scope calls |
| Per-call binding | `DelegationEnvelope` with `agent_sig` over `(DOMAIN‖vc_id‖nonce‖sha256(request))` |
| Instant revocation | `revokeDelegation()` on the T3N network invalidates the credential immediately |
| Tamper-proof audit | TEE-signed receipts — `issue-receipt` hashes `(agent‖action‖outcome‖timestamp‖vc_id)` |
| Replay protection | 16-byte random nonce per call, TEE enforces single-use |

---

## Architecture

```
Python orchestration layer (demo/run_real_t3n_demo.py)
        │
        ▼ subprocess
TypeScript T3N bridge (t3n-bridge/src/index.ts)  ← @terminal3/t3n-sdk
        │
        ├── auth.ts      — handshake() + authenticate() → real DID
        ├── credential.ts— buildDelegationCredential + signCredential + buildEnvelope
        ├── register.ts  — tenant.contracts.register (effv3-gateway WASM)
        └── gateway.ts   — executeAndDecode: authorize-action, issue-receipt, get-policy
                │
                ▼ T3N testnet HTTP
        Hardware TEE (effv3-gateway contract — Rust/WASM)
        └── contract/src/lib.rs — validates envelope, enforces scope, issues receipts
```

---

## What Is Real vs Pending Credits

| Component | Status |
|---|---|
| T3N auth: `handshake()` + `authenticate()` | **REAL** — live testnet |
| DID from T3N session | **REAL** — `did:t3n:ad146e6861ac408900af7ece1f6e90976dad3a02` |
| `buildDelegationCredential()` | **REAL** — `@terminal3/t3n-sdk` |
| `signCredential()` EIP-191 | **REAL** — `@terminal3/t3n-sdk` |
| `validateCredentialBody()` | **REAL** — SDK validation passed |
| `buildInvocationPreimage()` + `signAgentInvocation()` | **REAL** — `@terminal3/t3n-sdk` |
| `revokeDelegation()` | **REAL** call — credit-blocked (returns InsufficientCredit) |
| effv3-gateway WASM contract | **COMPILED** — 200KB artifact ready to deploy |
| TEE: `authorize-action`, `issue-receipt`, `get-policy` | **Pending credits** |
| TEE negative tests | **Pending credits** |

Phases 1–2 (auth + credential lifecycle) run fully without credits.
Phase 3+ (TEE contract) requires credits to register and invoke.

---

## Quick Start

```bash
# Install TypeScript bridge deps
cd t3n-bridge && npm install

# Run the full demo (real T3N testnet)
T3N_API_KEY=0x<your_key> node --loader ts-node/esm src/index.ts

# Or via Python orchestration layer
cd ..
T3N_API_KEY=0x<your_key> python demo/run_real_t3n_demo.py
```

### Environment

| Variable | Purpose |
|---|---|
| `T3N_API_KEY` | Ethereum private key (0x + 64 hex) from T3N ADK claim |
| `DID` | Your T3N DID (auto-derived from session if not set) |

---

## Proof

| Run | File | Key result |
|---|---|---|
| Session 1 | `proof/real_run_session1.txt` | Real DID + real credential + real envelope |

DID confirmed: `did:t3n:ad146e6861ac408900af7ece1f6e90976dad3a02`  
Credential: `buildDelegationCredential()` + `signCredential()` + `validateCredentialBody()` — all via `@terminal3/t3n-sdk`

---

## Contract

The `effv3-gateway` Rust/WASM contract (`contract/src/lib.rs`) exports three functions:

| Function | Input | What the TEE does |
|---|---|---|
| `authorize-action` | action + `__delegation_envelope` | Validates envelope, time window, scope → `ALLOW`/`DENY` |
| `issue-receipt` | agent_did + action + outcome + envelope | Computes `sha256(agent‖action‖outcome‖now‖vc_id)` → receipt |
| `get-policy` | — | Returns the active policy table (no credential needed) |

Build:
```bash
cd contract
cargo build --target wasm32-wasip2 --release
# Artifact: target/wasm32-wasip2/release/effv3_gateway.wasm (200KB)
```

---

## Security Properties

- **Envelope validation in TEE**: `agent_sig` and `nonce` (≥8 bytes) validated inside the enclave — not by the caller
- **Scope check in TEE**: `action` must appear in `credential.functions[]` — the credential is signed by the user and cannot be forged
- **Time check in TEE**: `not_after_secs` is compared against WASI wall-clock inside the enclave — the caller cannot spoof time
- **No secret leakage**: Private key never appears in logs or receipts — only `sha256(...)` fingerprints

---

## Known Gaps (Bug Report)

See `docs/BUGS_AND_DOC_GAPS.md` for 5 gaps found during integration:
- BUG-001: `tenant.contracts.register()` returns no `contractId` on re-registration
- BUG-002: `validateCredentialBody()` throws `UnsortedFunctions` with no indication in docs that the array must be alphabetically sorted
- BUG-003: No documented error code list for `executeAndDecode()` HTTP errors
- BUG-004: `getNodeUrl()` doc omits that `setEnvironment()` must be called first
- BUG-005: `revokeDelegation()` doc omits that it requires a credit balance

---

## License

MIT
