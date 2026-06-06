# SmallEFFV3 Part 2

> A governed AI transaction agent that transforms user intent into a policy-checked, human-approved Casper Testnet action with verifiable receipts.

**Repository:** `KAGEROU1107/SmallEffv3`
**Branch:** `smalleffv3part2`
**License:** MIT

---

## Problem

AI agents can parse natural-language intent, but turning that intent into a safe, verifiable blockchain transaction requires:

1. **Structured proposals** — converting free text into validated transaction parameters
2. **Deterministic policy** — enforcing limits, allowlists, and network restrictions
3. **Human authorization** — ensuring a human reviews and approves before signing
4. **Verifiable receipts** — cryptographic proof of what was decided and why

Without these, an AI could propose unsafe transactions, exceed limits, or act without human oversight.

---

## Solution

SmallEFFV3 Part 2 implements a governed transaction pipeline:

```
USER INTENT
    ↓
AI PROPOSAL (advisory only)
    ↓
STRUCTURED PROPOSAL (schema validation)
    ↓
POLICY ENGINE (deterministic checks)
    ↓
HUMAN REVIEW (explicit confirmation)
    ↓
CASPER TESTNET TRANSACTION
    ↓
GOVERNED RECEIPT (hash-bound, verifiable)
```

---

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env    # fill in values

# Run the existing identity + policy + receipt demo
python demo/run_demo.py

# Run tests
pytest tests/ -v
```

---

## Stack

- **Backend:** Python 3.12
- **Crypto:** `cryptography` library (Ed25519)
- **Cas:** Casper Testnet (via CSPR.click or direct RPC)
- **Testing:** pytest
- **CI:** GitHub Actions

---

## Project Structure

```
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── requirements.txt
├── .github/workflows/ci.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   ├── TESTNET_DEPLOYMENT.md
│   ├── DEMO_SCRIPT.md
│   └── examples/
│       └── example-receipt.json
├── src/
│   ├── terminal3_agent_auth_adapter.py
│   ├── governed_action_gate.py
│   └── execution_receipt.py
├── demo/
│   ├── run_demo.py
│   └── sample_sanitized_receipts/
├── tests/
│   ├── test_valid_identity.py
│   ├── test_forbidden_action.py
│   ├── test_invalid_identity.py
│   ├── test_replay_denial.py
│   └── test_receipt_integrity.py
└── runtime/receipts/    (gitignored)
```

---

## Test Coverage

```bash
pytest tests/ -v
```

`15/15 tests passing.`

---

## Status

`SCAFFOLDED` — Phase 0 complete. Core identity/policy/receipt components from Part 1 are preserved. Part 2 build proceeds from here.

---

## License

MIT — see [LICENSE](LICENSE)
