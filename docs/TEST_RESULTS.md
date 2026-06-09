# Test Results

Last verified: 2026-06-09

These results were run with a local uncommitted `.env` containing:

- `T3N_API_KEY`
- `DID`
- `T3_MOCK=false`

The raw key is intentionally not committed or printed.

## T3N ADK Developer Key Proof

Command:

```bash
python demo/run_t3n_token_demo.py
```

Result:

```text
T3N token demo
  result       : PASS
  mock_mode    : false
  did_bound    : True
  proof_signed : True
  decision     : ALLOW
  receipt_ok   : True
  no_secret    : True
```

## End-to-End Demo

Command:

```bash
python demo/run_demo.py
```

Result:

```text
SUMMARY: 5/5 scenarios passed
```

## Unit Tests

Command:

```bash
python -m pytest tests -q
```

Result:

```text
12 passed
```

## Optional Legacy HTTP Diagnostic

Command:

```bash
python demo/check_t3n_api.py
```

Result:

```text
Terminal 3 API check
  status       : 401
  api_ok       : False
  did_returned : False
  did_matches  : False
  error        : unauthorized
  note         : HTTP API credential check failed; local T3N token proof demo is separate.
```

Interpretation:

- The ADK developer-key proof path passes with `T3_MOCK=false`.
- The governed action path signs the proof, binds the DID, allows the valid action, verifies the receipt, and does not leak the key.
- The legacy Terminal 3 HTTP `/v1/did` diagnostic rejects the current test key as an HTTP API token, so it is not used as the primary ADK proof test.
