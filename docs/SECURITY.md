# Security Model — SmallEFFV3 Part 2

> **This is a prototype. Not production-ready.**
> Intended for educational, demonstrative, and hackathon purposes only.

---

## Authority Chain

```
USER INTENT
    ↓
AI ADVISORY PROPOSAL
    ↓
STRICT SCHEMA VALIDATION
    ↓
DETERMINISTIC POLICY ENGINE
    ↓
HUMAN REVIEW
    ↓
WALLET SIGNATURE
    ↓
CASPER TESTNET TRANSACTION
    ↓
TRANSACTION RECEIPT
```

## Non-Negotiable Rules

- **AI authority:** advisory only
- **Final authorization:** human wallet signature
- **Blockchain network:** Casper Testnet only
- **Transaction execution:** deterministic approved adapter only
- **Private keys:** never exposed to the model
- **Secrets:** environment variables only
- **Production funds:** forbidden

## What Is Protected

| Threat | Mitigation |
|--------|------------|
| AI overreach | AI output is advisory only — policy engine is deterministic |
| Policy bypass | Hardcoded allowlist, no LLM involvement |
| Replay attacks | Proposal hash binding + nonce system (from Part 1) |
| Receipt tampering | SHA-256 hash of canonical JSON |
| Key leakage | Raw keys never in outputs, logs, or receipts |
| Mainnet exposure | Network allowlist rejects non-testnet |
| Amount overflow | Configurable max transfer limit |
| Unapproved recipients | Allowlist check before execution |

## What Is NOT Protected

| Gap | Detail |
|-----|--------|
| Network security | No TLS enforcement — assumes secure channel |
| Key storage | API key in env var — no HSM or secure enclave |
| DoS | No rate limiting on proposal creation |
| Key rotation | No revocation mechanism |
| Distributed nonce | Local filesystem only |
| Contract audit | Prototype contract — not formally audited |
| Wallet security | Depends on CSPR.click or external wallet |

## Prototype Limitations

- Testnet only — never use with production funds
- Single action type (TRANSFER_CSPR) — not a general-purpose agent
- No autonomous loops — human must confirm each action
- Contract deployment requires separate Rust/Odra toolchain
- CSPR.click integration requires API key setup
