# Reviewer Guide

This repo's Terminal 3-related implementation is concentrated in a small set of files.

## Start Here

- `src/terminal3_agent_auth_adapter.py`
  - Reads `TERMINAL3_API_KEY`
  - Derives an Ed25519 private key from the 32-byte seed
  - Signs action requests
  - Verifies signed action proofs
- `src/governed_action_gate.py`
  - Verifies the incoming proof
  - Applies allow/deny policy
  - Prevents nonce replay
- `src/execution_receipt.py`
  - Builds and verifies tamper-evident execution receipts

## Fastest Proof Points

- `tests/test_valid_identity.py`
  - Valid signed proof -> allowed action -> verifiable receipt
- `tests/test_replay_denial.py`
  - Same nonce reused -> denied with `NONCE_REPLAYED`
- `demo/run_demo.py`
  - End-to-end demo flow with sanitized receipts

## Scope Clarification

What is implemented in this repo:

- Local cryptographic auth adapter around the Terminal 3 API key
- Governed action gate with policy and replay checks
- Receipt generation and verification

What is not claimed here:

- A full hosted Terminal 3 backend
- Remote attestation infrastructure
- A production-complete official SDK drop-in

This project demonstrates the governed execution pattern using a real Ed25519 proof flow and a clear audit trail.

## Suggested Review Commands

```bash
pytest tests/ -v
python demo/run_demo.py
```
