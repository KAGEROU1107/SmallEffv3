# Reviewer Guide

This repo's Terminal 3-related implementation is concentrated in a small set of files.

## Start Here

- `src/terminal3_agent_auth_adapter.py`
  - Reads the T3N ADK developer key from `T3N_API_KEY`
  - Binds `DID` into each action proof
  - Derives an Ed25519 private key from the 32-byte seed
  - Signs action requests
  - Verifies signed action proofs
- `demo/run_t3n_token_demo.py`
  - Uses the configured `T3N_API_KEY` and `DID` with `T3_MOCK=false`
  - Signs an action proof and verifies the governed path without exposing the token
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
  - Optional legacy Terminal 3 HTTP token/DID check with sanitized output

## Scope Clarification

What is implemented in this repo:

- T3N ADK developer-key proof flow
- Local cryptographic auth adapter around the T3N key and DID
- Governed action gate with policy and replay checks
- Receipt generation and verification

What is not claimed here:

- A hosted T3N node or remote MCP server
- Full TEE contract deployment/execution
- Remote attestation infrastructure
- A production-complete official SDK drop-in

This project demonstrates the governed execution pattern using a configured T3N ADK developer key and DID, a real proof flow, and a clear audit trail.

## Suggested Review Commands

```bash
pytest tests/ -v
python demo/run_t3n_token_demo.py
python demo/run_demo.py
```

Use `python demo/check_t3n_api.py --strict` only when the supplied key is expected to be accepted by Terminal 3's older hosted HTTP API.
