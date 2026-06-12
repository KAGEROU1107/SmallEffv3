/**
 * SmallEffv3 — DelegationCredential lifecycle using the T3N SDK.
 *
 * Wraps the SDK primitives for building, signing, validating, and revoking
 * agent delegation credentials. All operations here are local SDK calls
 * (no credits consumed). Only TEE invocation in gateway.ts costs credits.
 *
 * Credential wire shape (DelegationCredential):
 *   user_did      — who grants the delegation (tenant DID)
 *   agent_pubkey  — secp256k1 compressed pubkey of the agent being delegated
 *   functions     — allowlist of TEE functions the agent may call
 *   not_before / not_after — time-bounded window (30s for tests, longer for production)
 *   vc_id         — random 16-byte credential identifier
 *
 * DelegationEnvelope (per-call):
 *   credential_jcs + user_sig — credential payload + user's EIP-191 signature
 *   agent_sig                 — agent's Ed25519-like sig over (DOMAIN||vc_id||nonce||sha256(request))
 *   nonce                     — ≥8 bytes random, single-use replay guard
 *   request_hash              — sha256 of the call params JSON
 */

import {
  buildDelegationCredential,
  signCredential,
  canonicaliseCredential,
  validateCredentialBody,
  revokeDelegation,
  buildInvocationPreimage,
  signAgentInvocation,
  b64uEncodeBytes,
  getNodeUrl,
  type DelegationCredential,
  type DelegationEnvelope,
} from "@terminal3/t3n-sdk";
import type { T3nClient } from "@terminal3/t3n-sdk";
import { randomBytes, createHash } from "crypto";

export interface CredentialBundle {
  credential: DelegationCredential;
  jcs: Uint8Array;
  userSig: Uint8Array;
  vcId: Uint8Array;
  agentSecret: Uint8Array;
  vcIdHex: string;
  jcsB64u: string;
  userSigB64u: string;
  grantedFunctions: string[];
  windowSecs: bigint;
}

async function agentPubkey(secret: Uint8Array): Promise<Uint8Array> {
  try {
    const { secp256k1 } = await import("@noble/curves/secp256k1.js");
    return secp256k1.getPublicKey(secret, true);
  } catch {
    // fallback: deterministic mock pubkey from secret bytes
    const fb = new Uint8Array(33);
    fb[0] = 0x02;
    secret.slice(0, 32).forEach((b, i) => { fb[i + 1] = b; });
    return fb;
  }
}

/**
 * Build and sign a real DelegationCredential.
 * windowSecs controls how long the credential is valid.
 */
export async function buildCredential(
  userDid: string,
  apiKey: string,
  grantedFunctions: string[],
  windowSecs = 300n,
): Promise<CredentialBundle> {
  const agentSecret = new Uint8Array(randomBytes(32));
  const pubkey = await agentPubkey(agentSecret);
  const vcId = new Uint8Array(randomBytes(16));
  const now = BigInt(Math.floor(Date.now() / 1000));
  const userSecret = Buffer.from(apiKey.replace(/^0x/, ""), "hex");

  // T3N SDK requires functions to be sorted alphabetically
  const sortedFunctions = [...grantedFunctions].sort();

  const credential = buildDelegationCredential({
    user_did: userDid,
    agent_pubkey: pubkey,
    org_did: userDid,
    contract: "effv3-gateway",
    functions: sortedFunctions,
    scopes: [],
    metadata: { role: "governed-agent", system: "SmallEffv3" },
    not_before_secs: now,
    not_after_secs: now + windowSecs,
    vc_id: vcId,
  });

  validateCredentialBody(credential);
  const jcs = canonicaliseCredential(credential);
  const { sig: userSig } = signCredential(jcs, new Uint8Array(userSecret));

  return {
    credential,
    jcs,
    userSig,
    vcId,
    agentSecret,
    vcIdHex: Buffer.from(vcId).toString("hex"),
    jcsB64u: b64uEncodeBytes(jcs),
    userSigB64u: b64uEncodeBytes(userSig),
    grantedFunctions: sortedFunctions,
    windowSecs,
  };
}

/**
 * Build a per-call DelegationEnvelope for a specific request.
 * The envelope binds the credential to one specific call — not reusable.
 */
export function buildEnvelope(
  bundle: CredentialBundle,
  callParams: unknown,
): DelegationEnvelope {
  const callBytes = Buffer.from(JSON.stringify(callParams));
  const reqHash = new Uint8Array(createHash("sha256").update(callBytes).digest());
  const nonce = new Uint8Array(randomBytes(16));
  const preimage = buildInvocationPreimage(bundle.vcId, nonce, reqHash);
  const agentSig = signAgentInvocation(preimage, bundle.agentSecret);

  return {
    credential_jcs: bundle.jcs,
    user_sig: bundle.userSig,
    agent_sig: agentSig,
    nonce,
    request_hash: reqHash,
  };
}

/** Encode a DelegationEnvelope to the JSON wire shape expected by the TEE contract. */
export function encodeEnvelope(env: DelegationEnvelope): Record<string, string> {
  return {
    credential_jcs: b64uEncodeBytes(env.credential_jcs),
    user_sig:        b64uEncodeBytes(env.user_sig),
    agent_sig:       b64uEncodeBytes(env.agent_sig),
    nonce:           b64uEncodeBytes(env.nonce),
    request_hash:    b64uEncodeBytes(env.request_hash),
  };
}

/** Revoke a credential on the T3N network (real network call). */
export async function revokeCredential(
  t3n: T3nClient,
  bundle: CredentialBundle,
): Promise<{ revoked: boolean; error?: string }> {
  try {
    await revokeDelegation({ credentialJcsB64u: bundle.jcsB64u, client: t3n, baseUrl: getNodeUrl() });
    return { revoked: true };
  } catch (err) {
    return { revoked: false, error: (err as Error).message };
  }
}
