# Buildathon Checklist — SmallEFFV3 Part 2

## Qualification Round Requirements

- [x] Public GitHub repository (`KAGEROU1107/SmallEffv3` — `smalleffv3part2` branch)
- [x] Original project (builds on Part 1 identity/policy/receipt core)
- [ ] Working application (Phase 1-2 complete, Phase 6 pending)
- [ ] Casper Testnet deployment (requires Rust/Odra toolchain)
- [ ] Transaction-producing on-chain component (requires Testnet deployment)
- [ ] Smart contract source (Phase 3)
- [ ] Contract hash (after deployment)
- [ ] Transaction hash (after submission)
- [x] README
- [x] Setup instructions
- [ ] Demo video (final step)
- [ ] Screenshots (after Testnet deployment)
- [x] License (MIT)
- [x] Security limitations documented
- [ ] Roadmap

## Implementation Status

### Phase 0 — Branch and Repository Correction ✓
- [x] Branch `smalleffv3part2` created
- [x] Legacy files preserved
- [x] EFF V3 leakage removed
- [x] Secret-safe `.gitignore`
- [x] CI updated

### Phase 1 — Core Governance Foundation ✓
- [x] Proposal schema (`src/proposal_schema.py`)
- [x] Deterministic policy engine (`src/policy_engine.py`)
- [x] Governed receipt generator (`src/governed_receipt.py`)
- [x] Human confirmation (`src/human_confirmation.py`)
- [x] Unit tests (24 new tests)
- [x] Example receipt (`docs/examples/example-receipt.json`)

### Phase 2 — AI Advisory Adapter (pending)
- [ ] OpenRouter adapter
- [ ] Secondary model fallback
- [ ] JSON output validation
- [ ] Manual proposal fallback

### Phase 3 — Casper Contract (pending)
- [ ] Odra contract scaffold
- [ ] `record_proposal` entry point
- [ ] Contract tests

### Phase 4 — Casper Adapter (pending)
- [ ] Testnet connection
- [ ] Transaction building
- [ ] Wallet signing path

### Phase 5 — Receipt and Confirmation Flow (pending)
- [ ] Full integration
- [ ] End-to-end tests

### Phase 6 — User Interface (pending)
- [ ] Web interface or enhanced CLI
- [ ] Intent input
- [ ] Proposal review
- [ ] Confirmation flow

### Phase 7 — Testnet Deployment (pending)
- [ ] Contract deployment
- [ ] Transaction submission
- [ ] Evidence documentation

### Phase 8 — Submission Package (pending)
- [ ] Final README
- [ ] Demo video
- [ ] Screenshots
- [ ] Checklist completion
