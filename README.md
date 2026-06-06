# GUNGAN-FRAME — Multi-Persona Agent Orchestrator × Casper

> **Casper Agentic Buildathon 2026 — Qualification Round Submission**
> EFF V3 Verifiable Governed Agent Gateway + Casper Network Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![EFF V3](https://img.shields.io/badge/EFF-V3-green.svg)](https://github.com/KAGEROU1107/SmallEffv3)
[![Casper](https://img.shields.io/badge/Casper-Testnet-orange.svg)](https://www.casper.network/ai)

---

## What Is This?

A **multi-agent orchestration system** that coordinates 6 specialized AI personas to autonomously:
1. **Analyze** Casper DeFi opportunities (NOCTIS — forensic analyst)
2. **Formulate** strategy (KAGEROU — strategist)
3. **Validate** compliance (HIMERU — ethics reviewer)
4. **Execute** transactions on Casper Testnet (EXIA → CSPR.click)
5. **Verify** outcomes (RX-0 — data integrity guardian)
6. **Log** everything to immutable ARCLOG (VELVET_ARC — archivist)

Every action is gated by the **TRIAD governance protocol** and produces **hash-bound receipts** — no agent can act without consensus, no action goes unrecorded.

---

## Architecture

```
Agent Swarm (OpenRouter Free Models)
    │
    ▼
┌─────────────────────────────────────────────┐
│         GUNGAN-FRAME Orchestrator           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │  NOCTIS  │ │  EXIA    │ │ KAGEROU  │    │
│  │ Analyst  │ │ Engineer │ │Strategist│    │
│  └──────────┘ └──────────┘ └──────────┘    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │  HIMERU  │ │  RX-0    │ │ VELVET   │    │
│  │Compliance│ │ Auditor  │ │  ARC     │    │
│  └──────────┘ └──────────┘ └──────────┘    │
└──────────────────┬──────────────────────────┘
                   │
    ┌──────────────▼──────────────┐
    │       TRIAD GATE            │  ← Governance: 3-persona deliberation
    │  KAGEROU + HIMERU + NOCTIS  │     Free models cannot issue PASS
    └──────────────┬──────────────┘
                   │
    ┌──────────────▼──────────────┐
    │   Governed Model Router     │  ← V5.2, 13 slots, 5 keys, hash-only receipts
    │   (OpenRouter + ILMU)       │     330 total attempts, circuit breaker
    └──────────────┬──────────────┘
                   │
    ┌──────────────▼──────────────┐
    │   Casper Integration Layer  │
    │  ┌─────────┐ ┌──────────┐  │
    │  │ MCP     │ │CSPR.click│  │  ← On-chain queries + tx signing
    │  │ Server  │ │  Skill   │  │
    │  └─────────┘ └──────────┘  │
    │  ┌─────────┐ ┌──────────┐  │
    │  │  x402   │ │CSPR.cloud│  │  ← Micropayments + middleware
    │  │ Payment │ │   API    │  │
    │  └─────────┘ └──────────┘  │
    └──────────────┬──────────────┘
                   │
              ┌────▼────┐
              │ Testnet │
              └─────────┘
```

---

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env    # add OPENROUTER_SUBAGENT_KEY + CSPR_CLICK_API_KEY

# List available personas
python src/orchestrator.py --list-personas

# Run with specific personas
python src/orchestrator.py --brief "Analyze Casper testnet yield opportunities" \
  --personas NOCTIS,EXIA,KAGEROU,HIMERU,RX-0 --casper

# Full demo with all 6 personas + Casper integration + TRIAD gate
python src/orchestrator.py --demo --emit-json
```

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENROUTER_SUBAGENT_KEY` | Yes | OpenRouter API key for free-model personas |
| `OPENROUTER_API_KEY_1..5` | No | Multi-key rotation (V5.2 governed router) |
| `ILMUCHAT_API_KEY` | No | ILMU Chat terminal fallback |
| `CSPR_CLICK_API_KEY` | No | Casper Testnet wallet + tx signing |
| `T3_MOCK` | No | Use mock crypto for local dev (`true`/`false`) |

---

## Agent Personas

| Persona | Role | Model Lane | Casper Action |
|---------|------|------------|---------------|
| **KAGEROU** | Strategist/Orchestrator | `deepseek-v4-flash:free` | Proposes yield opportunities, initiates deliberation |
| **NOCTIS** | Forensic Analyst | `qwen3-next-80b:free` | On-chain data analysis, anomaly detection |
| **EXIA** | Execution Engine | `llama-3.3-70b:free` | Signs tx via CSPR.click, queries MCP |
| **HIMERU** | Compliance Officer | `gemma-4-31b-it:free` | Policy validation, forbidden-action blocker |
| **RX-0** | Data Integrity | `nemotron-3-super:free` | Receipt verification, reputation scoring |
| **VELVET_ARC** | Archivist | `llama-3.3-70b:free` | ARCLOG scene logging, instinct compression |

---

## Governance Model

### TRIAD Gate
Every action requires consensus from 3 reviewer personas:
1. **KAGEROU** — Is the strategy sound?
2. **HIMERU** — Is it compliant?
3. **NOCTIS** — Is the evidence solid?

Free-model outputs provide evidence but **cannot issue PASS alone** — only the main engine can authorize execution.

### Receipt Ledger
Every TRIAD verdict and agent action produces a hash-bound receipt:
- `sha256(canonical_json(receipt))` as integrity proof
- No raw secrets, prompts, or keys in receipts
- Tamper-evident: any mutation breaks the hash

---

## Test Coverage

```bash
pytest tests/ -v
```

| File | Tests | Coverage |
|------|-------|----------|
| `test_valid_identity.py` | 3 | Key derivation, signing, verification |
| `test_forbidden_action.py` | 3 | POLICY_MODIFY, PERSONA_WRITE, unknown denied |
| `test_invalid_identity.py` | 3 | Missing proof, garbage sig, missing nonce |
| `test_replay_denial.py` | 2 | Nonce replay → NONCE_REPLAYED |
| `test_receipt_integrity.py` | 4 | Tamper detection, deny receipt, fingerprint |

**15/15 tests passing.**

---

## Known Limitations

- Odra smart contracts not yet compiled (requires Rust toolchain)
- Casper Testnet tx signing requires `CSPR_CLICK_API_KEY`
- x402 micropayment facilitator not yet integrated
- MCP server calls are mocked in demo mode

## Roadmap

- [ ] Deploy AgentRegistry contract on Casper Testnet (Odra)
- [ ] Implement x402 micropayment flow for agent-to-agent payments
- [ ] Add ActionReceiptLedger on-chain contract
- [ ] Build web dashboard for real-time agent monitoring
- [ ] Integrate CSPR.trade MCP for live DeFi data
- [ ] Multi-agent DAO governance execution

---

## License

MIT — see [LICENSE](LICENSE)
