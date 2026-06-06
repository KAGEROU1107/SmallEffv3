# Architecture — SmallEFFV3 Part 2

## System Flow

```
┌───────────────────────────────────────────────┐
│ USER INTENT                                   │
│ "Transfer 5 test CSPR to approved recipient" │
└──────────────────────┬────────────────────────┘
                       ▼
┌───────────────────────────────────────────────┐
│ AI PROPOSAL ADAPTER                           │
│ advisory only                                 │
└──────────────────────┬────────────────────────┘
                       ▼
┌───────────────────────────────────────────────┐
│ STRICT PROPOSAL SCHEMA                        │
│ malformed output rejected                     │
└──────────────────────┬────────────────────────┘
                       ▼
┌───────────────────────────────────────────────┐
│ DETERMINISTIC POLICY ENGINE                   │
│ action · network · recipient · amount         │
└──────────────────────┬────────────────────────┘
                       │ deny
                       ├──────────────► STOP
                       ▼ allow
┌───────────────────────────────────────────────┐
│ HUMAN REVIEW                                  │
│ exact action and proposal hash displayed      │
└──────────────────────┬────────────────────────┘
                       │ reject
                       ├──────────────► STOP
                       ▼ confirm
┌───────────────────────────────────────────────┐
│ CASPER WALLET SIGNATURE                       │
│ human authority                               │
└──────────────────────┬────────────────────────┘
                       ▼
┌───────────────────────────────────────────────┐
│ CASPER TESTNET TRANSACTION                    │
│ transaction-producing on-chain component      │
└──────────────────────┬────────────────────────┘
                       ▼
┌───────────────────────────────────────────────┐
│ ON-CHAIN GOVERNED PROPOSAL RECORD             │
└──────────────────────┬────────────────────────┘
                       ▼
┌───────────────────────────────────────────────┐
│ GOVERNED RECEIPT                              │
│ proposal + policy + transaction lineage       │
└───────────────────────────────────────────────┘
```

## Components

### Identity Layer (from Part 1)
- `terminal3_agent_auth_adapter.py` — Ed25519 key derivation, signing, verification
- `governed_action_gate.py` — Policy enforcement, nonce replay protection
- `execution_receipt.py` — Hash-bound receipt generation

### Proposal Layer (Part 2 — new)
- `src/proposal_schema.py` — Structured proposal validation
- `src/proposal_hash.py` — SHA-256 canonical hashing
- `src/policy_engine.py` — Deterministic policy checks

### Casper Layer (Part 2 — new)
- `src/casper/adapter.py` — Casper Testnet connection, tx building
- `src/casper/contract.py` — Governed receipt contract interface
- `src/casper/wallet.py` — Wallet signing (human-approved only)

### Receipt Layer (Part 2 — new)
- `src/receipt_generator.py` — Full governed receipt with lineage

## Authority Model

```
AI authority:        advisory only
Final authorization: human wallet signature
Blockchain network:  Casper Testnet only
Transaction execution: deterministic approved adapter only
Private keys:        never exposed to the model
Secrets:             environment variables only
Production funds:    forbidden
```

## Non-Negotiable Rules

- AI cannot sign transactions
- AI cannot directly execute arbitrary contract calls
- Wallet private keys never embedded in code
- Seed phrases or private keys never logged
- `.env` never committed
- Failed policy validation blocks submission
- Explicit human approval required before signing
- No fabricated deploy hashes
- No success claims before verification
- Free-model output is never final authority
