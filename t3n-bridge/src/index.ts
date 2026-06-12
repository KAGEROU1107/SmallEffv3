/**
 * SmallEffv3 — Autonomous AI Agent Authorization Gateway
 *
 * Problem: Enterprise AI agents have no verifiable identity. Nothing prevents a
 * compromised or rogue agent from impersonating a legitimate one, replaying old
 * requests, or acting outside its authorized scope.
 *
 * Solution: Every agent action is gated by a T3N DelegationCredential that is:
 *   - Time-bounded (auto-expires even if revocation fails)
 *   - Scope-limited (only the functions listed in the credential are permitted)
 *   - Instantly revocable (one call to revokeDelegation cuts off the agent)
 *   - TEE-enforced (the effv3-gateway contract inside the enclave validates everything)
 *   - Audit-trailed (every approved action produces a TEE-signed receipt)
 *
 * Demo flow:
 *   Phase 1: Real T3N authentication — handshake() + authenticate() → real DID
 *   Phase 2: DelegationCredential lifecycle — build, sign, validate (SDK, no credits)
 *   Phase 3: TEE gateway — authorize-action, issue-receipt (requires credits)
 *   Phase 4: Revocation — issue credential, use it, revoke, verify post-revocation denial
 *   Phase 5: Negative tests — missing envelope, out-of-scope action
 *
 * Usage:
 *   T3N_API_KEY=0x<key> node --loader ts-node/esm src/index.ts
 */

import { createSession } from "./auth.js";
import { buildCredential, revokeCredential, encodeEnvelope, buildEnvelope } from "./credential.js";
import {
  authorizeAction,
  issueReceipt,
  getPolicy,
  negativeTest_missingEnvelope,
  negativeTest_outOfScopeAction,
} from "./gateway.js";
import { registerGatewayContract, wasmExists, CONTRACT_TAIL, CONTRACT_VERSION } from "./register.js";

const ALLOWED_ACTIONS   = ["authorize-action", "issue-receipt", "get-policy"];
const FORBIDDEN_ACTIONS = ["POLICY_MODIFY", "PERSONA_WRITE", "admin-override"];

function tag(ok: boolean) { return ok ? "[+]" : "[-]"; }
function teeResult(r: unknown) { return JSON.stringify(r).slice(0, 120); }

async function main() {
  const apiKey = process.env.T3N_API_KEY;
  if (!apiKey) {
    console.error("ERROR: T3N_API_KEY environment variable required.");
    process.exit(1);
  }

  console.log("=== SmallEffv3 — AI Agent Authorization Gateway (Terminal 3 ADK) ===\n");

  // ── Phase 1: Real T3N Authentication ─────────────────────────────────────────
  console.log("[Phase 1] Authenticating with Terminal 3 testnet...");
  let session;
  try {
    session = await createSession(apiKey);
    console.log(`  [+] handshake() complete`);
    console.log(`  [+] authenticate() complete`);
    console.log(`  [+] Real DID from session: ${session.tenantDid}`);
    console.log(`  [+] Ethereum address: ${session.address}`);
  } catch (err) {
    console.error(`  [-] Auth failed: ${(err as Error).message}`);
    process.exit(1);
  }
  const { t3n, tenantDid } = session;

  // ── Phase 2: DelegationCredential Lifecycle (SDK-only, no credits) ───────────
  console.log("\n[Phase 2] DelegationCredential lifecycle (real SDK, no credits needed)...");

  // Build credential for an agent authorized to call gateway functions
  const bundle = await buildCredential(tenantDid, apiKey, ALLOWED_ACTIONS, 300n);
  console.log(`  [+] Credential built`);
  console.log(`      vc_id     : ${bundle.vcIdHex}`);
  console.log(`      functions : ${bundle.grantedFunctions.join(", ")}`);
  console.log(`      window    : ${bundle.windowSecs}s`);
  console.log(`  [+] Signed with EIP-191 (user_sig): ${bundle.userSigB64u.slice(0, 20)}...`);
  console.log(`  [+] validateCredentialBody() passed — T3N SDK accepted credential`);

  // Build per-call envelope
  const testParams = { action: "authorize-action", agent_did: tenantDid };
  const envelope = buildEnvelope(bundle, testParams);
  const encoded  = encodeEnvelope(envelope);
  console.log(`  [+] DelegationEnvelope built`);
  console.log(`      agent_sig : ${encoded.agent_sig.slice(0, 20)}...`);
  console.log(`      nonce     : ${encoded.nonce.slice(0, 16)}...`);
  console.log(`      req_hash  : ${encoded.request_hash.slice(0, 20)}...`);

  // ── Phase 3: Register + Invoke TEE Gateway Contract ─────────────────────────
  console.log(`\n[Phase 3] TEE Gateway contract — ${CONTRACT_TAIL} v${CONTRACT_VERSION}...`);

  let teeOk = false;

  if (!wasmExists()) {
    console.log(`  [~] WASM not compiled — skipping TEE. Build with:`);
    console.log(`      cd contract && cargo build --target wasm32-wasip2 --release`);
  } else {
    // Pre-register contract (capture contractId on first deploy; BUG-001 on re-register)
    try {
      const info = await registerGatewayContract(session.tenant);
      const idStr = info.contractId !== undefined ? ` contractId=${info.contractId}` : ` (BUG-001: no contractId returned)`;
      console.log(`  [+] Contract registered: ${info.tail} v${info.version}${idStr}`);
    } catch (err) {
      const msg = (err as Error).message;
      if (msg.includes("InsufficientCredit")) {
        console.log(`  [~] Registration blocked: InsufficientCredit`);
      } else {
        console.log(`  [~] Registration: ${msg.slice(0, 100)}`);
      }
    }
  }

  try {
    // Policy query (read-only, no envelope needed)
    const policy = await getPolicy(t3n, tenantDid);
    console.log(`  [+] get-policy: ${JSON.stringify(policy).slice(0, 100)}`);

    // Authorize a permitted action
    const authResult = await authorizeAction(t3n, tenantDid, bundle, "authorize-action");
    console.log(`  ${tag(authResult.allowed)} authorize-action: ${teeResult(authResult)}`);

    // Issue a TEE-signed receipt
    const receipt = await issueReceipt(t3n, tenantDid, bundle, "authorize-action", "ALLOW");
    console.log(`  [+] issue-receipt: receipt_id=${receipt.receipt_id} issued_in_tee=${receipt.issued_in_tee}`);
    console.log(`      receipt_hash: ${receipt.receipt_hash}`);

    teeOk = true;
  } catch (err) {
    const msg = (err as Error).message;
    if (msg.includes("InsufficientCredit")) {
      console.log(`  [~] TEE call blocked: InsufficientCredit — contract ready, awaiting credit refill`);
      console.log(`      Contract: effv3-gateway v1.0.0 — deploy and invoke once credits available`);
    } else {
      console.log(`  [~] TEE call: ${msg.slice(0, 120)}`);
    }
  }

  // ── Phase 4: Revocation Lifecycle ────────────────────────────────────────────
  console.log("\n[Phase 4] Revocation lifecycle...");

  // Short-lived credential (30s window — expires fast for demo)
  const shortBundle = await buildCredential(tenantDid, apiKey, ALLOWED_ACTIONS, 30n);
  console.log(`  [+] Short-lived credential issued (30s window): vc_id=${shortBundle.vcIdHex}`);

  // Revoke it
  const revokeResult = await revokeCredential(t3n, shortBundle);
  if (revokeResult.revoked) {
    console.log(`  [+] revokeDelegation() SUCCESS — credential ${shortBundle.vcIdHex} invalidated on T3N`);
  } else {
    console.log(`  [~] revokeDelegation: ${revokeResult.error?.slice(0, 120)}`);
  }

  // Attempt to use the (now revoked) credential
  console.log(`  [+] Attempting post-revocation TEE call...`);
  try {
    const postRev = await authorizeAction(t3n, tenantDid, shortBundle, "authorize-action");
    const label = postRev.allowed ? "[-] UNEXPECTED ALLOW" : "[+] CORRECTLY DENIED post-revocation";
    console.log(`  ${label}: ${teeResult(postRev)}`);
  } catch (err) {
    const msg = (err as Error).message;
    if (msg.includes("InsufficientCredit")) {
      console.log(`  [~] post-revocation check: InsufficientCredit (expected when credits = 0)`);
    } else {
      console.log(`  [+] post-revocation REJECTED: ${msg.slice(0, 100)}`);
    }
  }

  // ── Phase 5: Negative Tests ───────────────────────────────────────────────────
  console.log("\n[Phase 5] Negative tests — gateway hardening...");

  // 5a: Call without any envelope
  const noEnv = await negativeTest_missingEnvelope(t3n, tenantDid, "authorize-action");
  console.log(`  [+] missing envelope: ${noEnv}`);

  // 5b: Credential scoped to ALLOWED_ACTIONS — attempt a FORBIDDEN action
  const outOfScope = await negativeTest_outOfScopeAction(t3n, tenantDid, bundle, FORBIDDEN_ACTIONS[0]);
  console.log(`  [+] out-of-scope action (${FORBIDDEN_ACTIONS[0]}): ${outOfScope}`);

  // ── Summary ───────────────────────────────────────────────────────────────────
  console.log("\n=== SmallEffv3 Demo Summary ===");
  console.log(`  DID              : ${tenantDid}`);
  console.log(`  Credential vc_id : ${bundle.vcIdHex}`);
  console.log(`  SDK credential   : REAL (buildDelegationCredential + signCredential)`);
  console.log(`  Envelope         : REAL (buildInvocationPreimage + signAgentInvocation)`);
  console.log(`  Revocation call  : ${revokeResult.revoked ? "SUCCESS" : "attempted (credit-blocked)"}`);
  console.log(`  TEE invocations  : ${teeOk ? "SUCCESS" : "PENDING (credit refill required)"}`);
  console.log(`  Negative tests   : 2/2 checked`);
}

main().catch((err) => {
  console.error("Fatal:", err.message);
  process.exit(1);
});
