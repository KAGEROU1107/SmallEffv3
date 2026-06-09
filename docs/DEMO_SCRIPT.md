# Demo Script: Verifiable Governed Agent Gateway (EFFV3)

**[ACTION: Open terminal in project root, clear screen]**

Welcome, everyone. I’m here to show you the Verifiable Governed Agent Gateway — our solution for the Terminal 3 Agent Auth bounty at DoraHacks. Today, we’ll see how we bring cryptographic identity and policy enforcement to AI agents, so they can act with verifiable authority — or be stopped when they shouldn’t.

**[ACTION: Pause briefly, make eye contact]**

Let’s start with the problem. AI agents are becoming more autonomous — they’re reading files, modifying configurations, even writing to databases. But how do we know it’s *really* the agent we authorized? And how do we stop it from doing something dangerous, like changing system policies or impersonating another user? Right now, most agents operate on trust alone — no identity proof, no replay protection, no audit trail. That’s a risk we can’t afford.

**[ACTION: Switch to diagram file, zoom in]**

Here’s our architecture. At the heart is the agent — it holds a Terminal 3 API key, which is just a 32-byte hex string, the seed for an Ed25519 key pair. When the agent wants to act, it goes through three stages.

First, the `terminal3_agent_auth_adapter.py` — this is where identity is proven. In mock mode, it returns a fixture identity. In live mode, it uses the `cryptography` library to derive the private key from the API key and signs a challenge — proving possession without ever exposing the key.

Next, the `governed_action_gate.py` — this is the policy engine. It checks two things: is this action allowed by our hardcoded policy? And has this nonce been used before? We store each nonce as a file — if we try to create it again, we get a FileExistsError, which we treat as a replay attack. If either check fails, we return a denial code: ACTION_FORBIDDEN or NONCE_REPLAYED.

If it passes, we move to `execution_receipt.py` — which creates a sanitized, hash-bound receipt. We take the action details, the agent’s fingerprint (never the raw key), a timestamp, and then we hash the whole thing — putting that hash as the last field. This means anyone can verify the receipt hasn’t been tampered with, but we never include secrets.

The outputs are simple: ALLOW or DENY, with a denial reason if needed. And every output is marked `raw_secret_included=False` — so we know we’re not leaking anything sensitive.

**[ACTION: Switch to terminal, run demo script]**

Let’s see it in action. I’ll run our demo script.

```
python demo/run_demo.py
```

**[ACTION: Wait for output, then point to each section]**

Here we go. First — agent tries to READ_MEMORY. We see: ALLOW. Identity verified, nonce fresh, policy permits it. Good.

Next — agent tries POLICY_MODIFY. We see: DENY, with code ACTION_FORBIDDEN. Our policy says no — and we enforce it. The agent is stopped cold.

Now — what if there’s no identity? We simulate missing API key. Output: DENY, IDENTITY_MISSING. No key, no trust — we don’t even try to verify.

Finally — replay attack. We use the same nonce twice. First time: ALLOW. Second time: DENY, NONCE_REPLAYED. The gate caught it because the nonce file already existed. FileExistsError becomes our replay shield.

And look — over here in the `data/receipts/` folder — we have a receipt file. Let’s cat it.

**[ACTION: Show receipt file contents]**

See? It’s JSON: action, agent_fingerprint, timestamp, and then the hash field at the end. No raw key. No secrets. Just proof that this action happened, signed by the system, and verifiable by anyone who has the fingerprint.

**[ACTION: Switch to test directory, run pytest]**

Now, let’s make sure it’s not just demo magic. I’ll run our test suite.

```
python -m pytest tests/ -v
```

**[ACTION: Wait for tests to pass, point to green output]**

All tests pass. Valid identity? Pass. Invalid identity? Properly denied. Forbidden action? Blocked. Replay? Detected. Our logic holds under scrutiny.

**[ACTION: Return to main terminal, summarize]**

To wrap up — what’s real and what’s mocked? The crypto is real: we use the `cryptography` library for Ed25519 signing in live mode. The nonce store uses real filesystem locking via `open(x)`. The policy is hardcoded for now — but it’s designed to be pluggable. The receipt hashing is real and collision-resistant.

What’s mocked? In this demo, we set `T3_MOCK=true` so we don’t require a real Terminal 3 key — we use a fixture. In production, you’d unset that and provide your own API key. Also, we’re not connecting to a real agent framework — this is the gateway layer. And importantly: this is a hackathon prototype. It’s not production-ready yet — no rate limiting, no distributed nonce store, no key rotation. But the core ideas — verifiable identity, policy enforcement, replay resistance, and auditible receipts — are sound.

**[ACTION: Smile, conclude]**

Thanks for watching. We’ve shown how to make agent actions verifiable, governable, and accountable — without sacrificing security or leaking secrets. If you’d like to try it yourself, the code is open and ready to run. Let’s build agents we can trust — not just hope they behave.

**[ACTION: End recording]**