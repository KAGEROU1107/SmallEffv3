# Reviewer Guide

This repo's Terminal 3-related implementation is concentrated in a small set of files.

## Start Here

- `src/terminal3_api_client.py`
  - Sends `T3N_API_KEY` as Terminal 3's documented `x-api-token` header
  - Calls `GET /v1/did`
  - Compares returned DID with the configured `DID`
- `src/terminal3_agent_auth_adapter.py`
  - Reads `T3N_API_KEY` with `TERMINAL3_API_KEY` as a compatibility alias
  - Binds `DID` into each action proof
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
- `demo/check_t3n_api.py`
  - Live Terminal 3 token/DID API check with sanitized output

## Scope Clarification

What is implemented in this repo:

- Terminal 3 token API check against `GET /v1/did`
- Local cryptographic auth adapter around the Terminal 3 key
- Governed action gate with policy and replay checks
- Receipt generation and verification

What is not claimed here:

- A full hosted Terminal 3 backend
- Remote attestation infrastructure
- A production-complete official SDK drop-in

This project demonstrates the governed execution pattern using Terminal 3 token/DID validation, a real Ed25519 proof flow, and a clear audit trail.

## Suggested Review Commands

```bash
pytest tests/ -v
python demo/check_t3n_api.py
python demo/run_demo.py
```
