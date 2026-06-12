/**
 * SmallEffv3 — TEE Gateway contract invocations.
 *
 * The effv3-gateway contract runs inside a T3N hardware TEE.
 * Three exported functions:
 *   authorize-action — validates DelegationEnvelope + scope, returns ALLOW/DENY
 *   issue-receipt    — creates a TEE-signed tamper-proof execution receipt
 *   get-policy       — returns the active policy table (read-only)
 *
 * All invocations go through t3n.executeAndDecode — real TEE execution.
 * If credits are 0 the T3N node returns InsufficientCredit; the caller handles it.
 */

import type { T3nClient } from "@terminal3/t3n-sdk";
import type { CredentialBundle } from "./credential.js";
import { buildEnvelope, encodeEnvelope } from "./credential.js";

const CONTRACT   = "effv3-gateway";
const VERSION    = "1.0.0";

function scriptName(tenantDid: string): string {
  return `z:${tenantDid.slice("did:t3n:".length)}:${CONTRACT}`;
}

async function call(
  t3n: T3nClient,
  tenantDid: string,
  fn: string,
  input: Record<string, unknown>,
): Promise<unknown> {
  return t3n.executeAndDecode({
    script_name: scriptName(tenantDid),
    script_version: VERSION,
    function_name: fn,
    input,
  });
}

export interface AuthorizeResult {
  allowed: boolean;
  reason: string;
  action: string;
  agent_fingerprint: string;
  authorized_at_epoch: number;
  processed_in_tee: boolean;
}

export interface ReceiptResult {
  receipt_id: string;
  agent_did: string;
  action: string;
  outcome: string;
  issued_in_tee: boolean;
  receipt_hash: string;
}

/**
 * Ask the TEE whether this agent may perform the action.
 * The DelegationEnvelope is built fresh for this specific request.
 */
export async function authorizeAction(
  t3n: T3nClient,
  tenantDid: string,
  bundle: CredentialBundle,
  action: string,
): Promise<AuthorizeResult> {
  const callParams = { action, agent_did: tenantDid };
  const envelope = buildEnvelope(bundle, callParams);

  const result = await call(t3n, tenantDid, "authorize-action", {
    action,
    agent_did: tenantDid,
    __delegation_envelope: encodeEnvelope(envelope),
  });

  return result as AuthorizeResult;
}

/**
 * Issue a TEE-signed execution receipt after an action completes.
 */
export async function issueReceipt(
  t3n: T3nClient,
  tenantDid: string,
  bundle: CredentialBundle,
  action: string,
  outcome: string,
): Promise<ReceiptResult> {
  const callParams = { action, outcome };
  const envelope = buildEnvelope(bundle, callParams);

  const result = await call(t3n, tenantDid, "issue-receipt", {
    agent_did: tenantDid,
    action,
    outcome,
    vc_id_hex: bundle.vcIdHex,
    __delegation_envelope: encodeEnvelope(envelope),
  });

  return result as ReceiptResult;
}

/**
 * Query the active policy table from the TEE (no credential needed — read-only).
 */
export async function getPolicy(
  t3n: T3nClient,
  tenantDid: string,
): Promise<Record<string, string>> {
  const result = await call(t3n, tenantDid, "get-policy", {});
  return result as Record<string, string>;
}

/**
 * Negative test: send a malformed envelope — TEE must reject it.
 * Returns the rejection message.
 */
export async function negativeTest_missingEnvelope(
  t3n: T3nClient,
  tenantDid: string,
  action: string,
): Promise<string> {
  try {
    await call(t3n, tenantDid, "authorize-action", { action, agent_did: tenantDid });
    return "UNEXPECTED ACCEPT — envelope was not required";
  } catch (err) {
    return `REJECTED: ${(err as Error).message.slice(0, 120)}`;
  }
}

export async function negativeTest_outOfScopeAction(
  t3n: T3nClient,
  tenantDid: string,
  bundle: CredentialBundle,
  forbiddenAction: string,
): Promise<string> {
  const callParams = { action: forbiddenAction, agent_did: tenantDid };
  const envelope = buildEnvelope(bundle, callParams);
  try {
    const r = await call(t3n, tenantDid, "authorize-action", {
      action: forbiddenAction,
      agent_did: tenantDid,
      __delegation_envelope: encodeEnvelope(envelope),
    });
    const result = r as AuthorizeResult;
    return result.allowed
      ? `UNEXPECTED ALLOW — scope check failed`
      : `CORRECTLY DENIED: ${result.reason}`;
  } catch (err) {
    return `REJECTED: ${(err as Error).message.slice(0, 120)}`;
  }
}
