# Architecture — Casper Agentic Buildathon 2026
# EFFV3 × Casper: Multi-Persona Autonomous Agent System

## Project Codename: GUNGAN-FRAME

A swarm of specialized AI agents that autonomously monitor, deliberate, and execute
on-chain actions on the Casper Network — each agent bound by cryptographic identity,
governance policy, and on-chain receipt.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GUNGAN- FRAME                             │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ KAGEROU  │  │  NOCTIS  │  │   EXIA   │  │ HIMERU   │   │
│  │ Strategist│  │ Analyst  │  │ Engineer │  │ Compliance│   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │          │
│       ▼              ▼              ▼              ▼          │
│  ┌──────────────────────────────────────────────────────┐     │
│  │           Agent Orchestrator (Cortex)                 │     │
│  │  Multi-agent deliberation + consensus protocol        │     │
│  └──────────────────────┬───────────────────────────────┘     │
│                         │                                     │
│  ┌──────────────────────▼───────────────────────────────┐     │
│  │        Terminal 3 Auth Adapter (existing)             │     │
│  │  Ed25519 identity · policy gate · nonce guard         │     │
│  └──────────────────────┬───────────────────────────────┘     │
│                         │                                     │
│  ┌──────────────────────▼───────────────────────────────┐     │
│  │           Casper Integration Layer                    │     │
│  │  MCP Client · CSPR.click · x402 · CSPR.cloud         │     │
│  └──────────────────────┬───────────────────────────────┘     │
│                         │                                     │
│                    ┌────▼────┐                                 │
│                    │ Testnet  │                                 │
│                    └─────────┘                                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              On-Chain Reputation Ledger               │     │
│  │  Agent identity · action history · trust scores       │     │
│  └──────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent Personas (V3 Full Cast)

| Persona | Role | Casper Action | Model Task |
|---------|------|---------------|------------|
| **KAGEROU** | Strategist/Orchestrator | Proposes yield opportunities, initiates deliberation | reason, analyse |
| **NOCTIS** | Forensic Analyst | Analyzes on-chain data, flags anomalies | analyse, classify |
| **EXIA** | Execution Engineer | Signs tx via CSPR.click, deploys contracts | parse, draft |
| **HIMERU** | Compliance Officer | Validates actions against policy, blocks forbidden | classify, reason |
| **RX-0** | Data Integrity Guardian | Verifies receipts, checks hashes, monitors | parse, analyse |
| **BARBATOS** | Rapid Executor | Fast tx signing for time-sensitive ops | draft |
| **VELVET_ARC** | Logging/Archival | ARCLOG compression, scene logging | summarize |

---

## Casper Integration Points

### 1. MCP Server (Casper Blockchain Queries)
- **Casper MCP Server** — query account balance, block info, deploy status
- **CSPR.trade MCP** — DEX price feeds, swap operations
- Used by: NOCTIS (market analysis), KAGEROU (yield data), RX-0 (verification)

### 2. CSPR.click AI Agent Skill
- Wallet creation on Casper Testnet
- Transaction signing via API key
- Used by: EXIA (contract deployment), BARBATOS (fast execution)

### 3. x402 Micropayments
- Agents pay per API call (market data, oracle queries)
- Facilitator pattern: agent signs payment proof, server responds with data
- Enables agent-to-agent commerce (e.g., NOCTIS pays EXIA for data processing)

### 4. Odra Smart Contracts (Testnet Deploy)
- **AgentRegistry** — register agent identities + fingerprints
- **ActionReceiptLedger** — on-chain receipt log (hash-bound, immutable)
- **ReputationTracker** — agent trust scores based on historical accuracy
- **ComplianceGate** — on-chain policy enforcement (forbidden action list)

### 5. CSPR.cloud API
- REST API for streamlined blockchain interaction
- Streaming API for real-time event monitoring
- Used by: all agents for lightweight queries

---

## Execution Flow (Single Action Cycle)

```
1. TRIGGER
   └─ External event (price threshold,定时 trigger, user command)

2. KAGEROU (Strategist)
   ├─ Receives trigger via orchestrator
   ├─ Queries Casper MCP for current state
   ├─ Proposes action: {type, target, amount, justification}
   └─ Broadcasts proposal to all agents

3. NOCTIS (Analyst)
   ├─ Pulls on-chain data via MCP
   ├─ Runs risk assessment
   └─ Returns: {risk_score, anomaly_flags, recommendation}

4. HIMERU (Compliance)
   ├─ Checks proposed action against policy
   ├─ Cross-references forbidden actions list
   └─ Returns: {compliance: PASS/FAIL, denial_code?}

5. EXIA (Engineer)
   ├─ If KAGEROU + NOCTIS + HIMERU all agree:
   ├─ Builds transaction payload
   ├─ Signs via CSPR.click skill
   └─ Submits to Casper Testnet

6. RX-0 (Auditor)
   ├─ Verifies tx was included in block
   ├─ Validates receipt hash matches expected
   ├─ Updates reputation score
   └─ Returns: {verified: bool, block_hash}

7. BARBATOS (Executor/Failsafe)
   └─ If primary tx fails: retry with adjusted params

8. VELVET_ARC (Logger)
   └─ Compresses scene into ARCLOG
   └─ Writes to on-chain receipt ledger
```

---

## Project Structure

```
SmallEffv3Part2/
├── src/
│   ├── terminal3_agent_auth_adapter.py    (existing — agent identity)
│   ├── governed_action_gate.py            (existing — policy enforcement)
│   ├── execution_receipt.py               (existing — receipt generation)
│   ├── casper_mcp_client.py               (NEW — MCP protocol client)
│   ├── cspr_click_skill.py                (NEW — wallet + tx signing)
│   ├── agent_orchestrator.py              (NEW — multi-agent deliberation)
│   ├── persona_registry.py                (NEW — persona definitions + prompts)
│   ├── reputation_tracker.py              (NEW — on-chain trust scores)
│   └── x402_client.py                     (NEW — micropayment client)
├── contracts/
│   ├── odra/
│   │   ├── agent_registry/                (NEW — Odra smart contract)
│   │   ├── action_receipt_ledger/         (NEW — on-chain receipt log)
│   │   └── reputation/                    (NEW — trust tracking)
│   └── wasm/                              (NEW — compiled WASM targets)
├── agents/
│   ├── strategist/                        (KAGEROU role definition)
│   ├── analyst/                           (NOCTIS role definition)
│   ├── engineer/                          (EXIA role definition)
│   ├── compliance/                        (HIMERU role definition)
│   ├── auditor/                           (RX-0 role definition)
│   └── executor/                          (BARBATOS role definition)
├── demo/
│   ├── run_demo.py                         (existing — updated with Casper scenarios)
│   └── casper_scenarios/                  (NEW — Casper-specific demo scripts)
├── tests/
│   ├── test_valid_identity.py              (existing)
│   ├── test_forbidden_action.py            (existing)
│   ├── test_invalid_identity.py            (existing)
│   ├── test_replay_denial.py               (existing)
│   ├── test_receipt_integrity.py           (existing)
│   ├── test_casper_mcp.py                  (NEW)
│   ├── test_agent_orchestrator.py          (NEW)
│   ├── test_reputation.py                  (NEW)
│   └── test_x402.py                        (NEW)
├── docs/
│   ├── ARCHITECTURE.md                     (this file)
│   ├── BUILD_CASPER.md                     (NEW — build guide)
│   ├── AGENT_PROTOCOL.md                   (NEW — agent deliberation protocol)
│   └── SECURITY_MODEL.md                   (existing)
├── requirements.txt
├── .env.example
├── README.md
└── .github/workflows/ci.yml
```

---

## Hackathon Deliverables Mapping

**Working Prototype on Casper Testnet:**
- CSPR.click skill creates a Testnet wallet
- Agent registers identity on AgentRegistry contract
- At least 1 on-chain transaction producing event
- Receipt logged to ActionReceiptLedger

**Open Source GitHub:**
- All code in this repo, MIT licensed
- README with architecture overview, setup instructions, demo walkthrough

**Demo Video:**
- Show: agent deliberation → policy check → tx signing → on-chain confirmation
- Show: dashboard with agent activity + receipt verification
- Show: community voting via CSPR.fans (screenshot/desktop recording)

**Community Voting:**
- Submit on CSPR.fans app
- Top 3 by votes = auto-advance to finals

**Judging Criteria Coverage:**
| Criterion | How We Cover It |
|-----------|-----------------|
| Technical Execution | Ed25519 auth + Odra contracts + MCP integration |
| Innovation & Originality | Multi-agent deliberation with on-chain governance |
| AI/Agentic Systems | 6 personas with distinct roles, autonomous execution |
| Real-World Applicability | DeFi yield routing + RWA oracle patterns |
| UX & Design | Terminal dashboard + receipt visualization |
| Working Smart Contracts | AgentRegistry + ActionReceiptLedger on Testnet |
| Long-Term Launch | Open source, roadmap in docs, social channels |
| Ecosystem Impact | Direct Casper integration, x402, MCP, Odra |

---

## Phase 0: Qualification Round Scope (June 1-30)

Since we have ~3 weeks, here's the realistic scope:

**Week 1 (June 6-12): Foundation**
- [x] Branch from terminal3 bounty
- [ ] Casper MCP client (query testnet state)
- [ ] CSPR.click skill integration (wallet + basic tx)
- [ ] Persona registry + agent orchestrator skeleton
- [ ] AgentRegistry Odra contract (Rust → WASM)

**Week 2 (June 13-19): Core Logic**
- [ ] Multi-agent deliberation protocol
- [ ] x402 client (micropayment)
- [ ] ActionReceiptLedger contract
- [ ] Reputation tracking
- [ ] Integration tests

**Week 3 (June 20-30): Ship**
- [ ] Demo scenarios (yield alert → agent swarm → tx)
- [ ] Dashboard (terminal UI or simple web)
- [ ] README + docs pass
- [ ] Demo video
- [ ] Submit on DoraHacks + CSPR.fans

---

## Known Risks

1. **Odra requires Rust toolchain** — if setup is complex, fallback: Python-based contract interaction via CLType JSON
2. **CSPR.click API may have rate limits** — implement retry with backoff
3. **MCP server may need auth** — budget time for auth flow
4. **Testnet faucet availability** — pre-fund wallet early

---

## Future Work (Post-Qualification)

- Multi-agent DAO governance (swarm voting on proposals)
- RWA oracle with verifiable identity
- Agent-to-agent x402 marketplace
- Cross-chain agent bridge
- Full V3 runtime migration to Casper mainnet
