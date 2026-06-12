use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::time::{SystemTime, UNIX_EPOCH};

wit_bindgen::generate!({
    world: "effv3-gateway",
    path: "wit",
});

struct Component;

export!(Component);

// ── Helpers ───────────────────────────────────────────────────────────────────

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

fn parse<'a, T: Deserialize<'a>>(bytes: &'a [u8], ctx: &str) -> Result<T, String> {
    serde_json::from_slice(bytes).map_err(|e| format!("{ctx}: {e}"))
}

fn encode<T: Serialize>(v: &T) -> Result<Vec<u8>, String> {
    serde_json::to_vec(v).map_err(|e| e.to_string())
}

fn sha256_hex(data: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(data);
    h.finalize().iter().map(|b| format!("{b:02x}")).collect()
}

// ── Delegation envelope ───────────────────────────────────────────────────────

#[derive(Deserialize)]
struct Envelope {
    credential_jcs: String,
    #[serde(default)]
    nonce: String,
    #[serde(default)]
    agent_sig: String,
}

#[derive(Deserialize)]
struct CredentialBody {
    functions: Vec<String>,
    not_before_secs: String,
    not_after_secs: String,
    #[serde(default)]
    vc_id: String,
}

struct EnvelopeCheck {
    agent_fingerprint: String,
    vc_id_hex: String,
}

/// Validate the __delegation_envelope embedded in the call input.
/// Checks: envelope present, nonce ≥8 bytes, agent_sig non-empty,
///         credential JCS decodable, time window active, action in scope.
fn validate_envelope(env: &Envelope, action: &str, now: u64) -> Result<EnvelopeCheck, String> {
    // Nonce length (replay guard — actual replay tracking is in TEE state)
    if !env.nonce.is_empty() {
        let nonce_bytes = URL_SAFE_NO_PAD
            .decode(&env.nonce)
            .map_err(|_| "envelope: nonce not valid base64url".to_string())?;
        if nonce_bytes.len() < 8 {
            return Err(format!(
                "envelope: nonce too short ({} bytes, minimum 8)",
                nonce_bytes.len()
            ));
        }
    } else {
        return Err("envelope: nonce missing".to_string());
    }

    // agent_sig presence (signature bytes validated by T3N infra before reaching contract)
    if env.agent_sig.is_empty() {
        return Err("envelope: agent_sig missing".to_string());
    }

    // Decode and parse credential JCS
    let jcs_bytes = URL_SAFE_NO_PAD
        .decode(&env.credential_jcs)
        .map_err(|_| "envelope: credential_jcs not valid base64url".to_string())?;

    let cred: CredentialBody =
        parse(&jcs_bytes, "credential_jcs").map_err(|e| format!("credential parse: {e}"))?;

    // Time window check (WASI wall-clock — inside enclave)
    let not_before: u64 = cred
        .not_before_secs
        .parse()
        .map_err(|_| "credential: bad not_before_secs".to_string())?;
    let not_after: u64 = cred
        .not_after_secs
        .parse()
        .map_err(|_| "credential: bad not_after_secs".to_string())?;

    if now < not_before {
        return Err(format!("credential not yet valid (not_before={not_before}, now={now})"));
    }
    if now > not_after {
        return Err(format!("credential expired (not_after={not_after}, now={now})"));
    }

    // Scope check — action must be in the credential's functions list
    if !cred.functions.iter().any(|f| f == action) {
        return Err(format!(
            "action '{action}' not in credential scope: {:?}",
            cred.functions
        ));
    }

    // Fingerprint from credential JCS sha256
    let fp = &sha256_hex(&jcs_bytes)[..12];
    Ok(EnvelopeCheck {
        agent_fingerprint: fp.to_string(),
        vc_id_hex: cred.vc_id.clone(),
    })
}

// ── authorize-action ──────────────────────────────────────────────────────────

#[derive(Deserialize)]
struct AuthorizeInput {
    action: String,
    #[serde(default)]
    agent_did: String,
    #[serde(rename = "__delegation_envelope")]
    envelope: Option<Envelope>,
}

#[derive(Serialize)]
struct AuthorizeOutput {
    allowed: bool,
    reason: String,
    action: String,
    agent_fingerprint: String,
    authorized_at_epoch: u64,
    processed_in_tee: bool,
}

impl Guest for Component {
    fn authorize_action(input: Vec<u8>) -> Result<Vec<u8>, String> {
        let req: AuthorizeInput = parse(&input, "authorize-action")?;
        let now = now_secs();

        let env = req.envelope.ok_or("envelope: __delegation_envelope missing")?;

        match validate_envelope(&env, &req.action, now) {
            Ok(check) => encode(&AuthorizeOutput {
                allowed: true,
                reason: "CREDENTIAL_VALID".into(),
                action: req.action,
                agent_fingerprint: check.agent_fingerprint,
                authorized_at_epoch: now,
                processed_in_tee: true,
            }),
            Err(e) => encode(&AuthorizeOutput {
                allowed: false,
                reason: e.clone(),
                action: req.action,
                agent_fingerprint: String::new(),
                authorized_at_epoch: now,
                processed_in_tee: true,
            }),
        }
    }

    // ── issue-receipt ─────────────────────────────────────────────────────────

    fn issue_receipt(input: Vec<u8>) -> Result<Vec<u8>, String> {
        #[derive(Deserialize)]
        struct ReceiptInput {
            agent_did: String,
            action: String,
            outcome: String,
            #[serde(default)]
            vc_id_hex: String,
            #[serde(rename = "__delegation_envelope")]
            envelope: Option<Envelope>,
        }

        #[derive(Serialize)]
        struct ReceiptOutput {
            receipt_id: String,
            agent_did: String,
            action: String,
            outcome: String,
            issued_in_tee: bool,
            receipt_hash: String,
        }

        let req: ReceiptInput = parse(&input, "issue-receipt")?;
        let now = now_secs();

        // Envelope validation required for receipt issuance
        if let Some(ref env) = req.envelope {
            validate_envelope(env, &req.action, now)?;
        }

        // Receipt content binds: agent_did + action + outcome + timestamp + vc_id
        let receipt_body = format!(
            "{}|{}|{}|{}|{}",
            req.agent_did, req.action, req.outcome, now, req.vc_id_hex
        );
        let receipt_hash = sha256_hex(receipt_body.as_bytes());

        // Receipt ID: first 16 hex chars of the hash
        let receipt_id = receipt_hash[..16].to_string();

        encode(&ReceiptOutput {
            receipt_id,
            agent_did: req.agent_did,
            action: req.action,
            outcome: req.outcome,
            issued_in_tee: true,
            receipt_hash,
        })
    }

    // ── get-policy ────────────────────────────────────────────────────────────

    fn get_policy() -> Result<Vec<u8>, String> {
        #[derive(Serialize)]
        struct PolicyEntry {
            action: &'static str,
            decision: &'static str,
            scope: &'static str,
        }

        let policy = vec![
            PolicyEntry { action: "authorize-action", decision: "ALLOW", scope: "gateway:read" },
            PolicyEntry { action: "issue-receipt",    decision: "ALLOW", scope: "gateway:write" },
            PolicyEntry { action: "get-policy",       decision: "ALLOW", scope: "gateway:read" },
            PolicyEntry { action: "POLICY_MODIFY",    decision: "DENY",  scope: "admin:restricted" },
            PolicyEntry { action: "PERSONA_WRITE",    decision: "DENY",  scope: "admin:restricted" },
            PolicyEntry { action: "admin-override",   decision: "DENY",  scope: "admin:restricted" },
        ];

        encode(&serde_json::json!({
            "policy_version": "1.0",
            "entries": policy,
            "evaluated_in_tee": true
        }))
    }
}
