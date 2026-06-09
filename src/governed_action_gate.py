import sys
import json
import hashlib
import datetime
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.terminal3_agent_auth_adapter import verify_action_request

POLICY = {
    "READ_MEMORY":  "ALLOW",
    "LIST_SKILLS":  "ALLOW",
    "POLICY_MODIFY": "DENY",
    "PERSONA_WRITE": "DENY",
}

NONCE_STORE_DIR = Path("data/nonce_store")
NONCE_STORE_DIR.mkdir(parents=True, exist_ok=True)

POLICY_VERSION = "1.0"

# Secrets to scan for in receipts (env var names — not values)
_SECRET_MARKERS = ["T3N_API_KEY", "TERMINAL3_API_KEY", "ILMUCHAT_API_KEY", "OPENROUTER", "0xdd"]


def _nonce_path(nonce: str) -> Path:
    """Use sha256 of nonce as filename — prevents path traversal."""
    safe_name = hashlib.sha256(nonce.encode()).hexdigest()
    return NONCE_STORE_DIR / f"{safe_name}.json"


def evaluate_action(proof: Dict[str, Any], action: str) -> Dict[str, Any]:
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    agent_fp = proof.get("agent_id", "unknown")

    # Require explicit nonce — do not auto-generate (Fix #3)
    nonce = proof.get("nonce")
    if not nonce:
        nonce_hash = None
        proof_hash = hashlib.sha256(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {
            "decision": "DENY",
            "action": action,
            "agent_fingerprint": agent_fp,
            "denial_code": "NONCE_MISSING",
            "nonce_consumed": None,
            "nonce_hash": nonce_hash,
            "proof_hash": proof_hash,
            "policy_version": POLICY_VERSION,
            "ts": ts,
        }

    # Verify signed action request (signature covers action + nonce + audience)
    ok, denial_code = verify_action_request(proof, action)
    if not ok:
        nonce_hash = hashlib.sha256(nonce.encode()).hexdigest()
        proof_hash = hashlib.sha256(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {
            "decision": "DENY",
            "action": action,
            "agent_fingerprint": agent_fp,
            "denial_code": denial_code,
            "nonce_consumed": None,
            "nonce_hash": nonce_hash,
            "proof_hash": proof_hash,
            "policy_version": POLICY_VERSION,
            "ts": ts,
        }

    # Policy check — default DENY for anything not explicitly allowed
    if POLICY.get(action, "DENY") == "DENY":
        nonce_hash = hashlib.sha256(nonce.encode()).hexdigest()
        proof_hash = hashlib.sha256(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {
            "decision": "DENY",
            "action": action,
            "agent_fingerprint": agent_fp,
            "denial_code": "ACTION_FORBIDDEN",
            "nonce_consumed": None,
            "nonce_hash": nonce_hash,
            "proof_hash": proof_hash,
            "policy_version": POLICY_VERSION,
            "ts": ts,
        }

    # Atomic nonce consumption — FileExistsError = replay (Fix #4 path traversal safe)
    nonce_hash = hashlib.sha256(nonce.encode()).hexdigest()
    proof_hash = hashlib.sha256(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    npath = _nonce_path(nonce)
    try:
        npath.parent.mkdir(parents=True, exist_ok=True)
        with open(npath, "x") as f:
            json.dump({"consumed_at": ts, "nonce_hash": nonce_hash, "action": action}, f)
    except FileExistsError:
        return {
            "decision": "DENY",
            "action": action,
            "agent_fingerprint": agent_fp,
            "denial_code": "NONCE_REPLAYED",
            "nonce_consumed": nonce,
            "nonce_hash": nonce_hash,
            "proof_hash": proof_hash,
            "policy_version": POLICY_VERSION,
            "ts": ts,
        }

    return {
        "decision": "ALLOW",
        "action": action,
        "agent_fingerprint": agent_fp,
        "denial_code": None,
        "nonce_consumed": nonce,
        "nonce_hash": nonce_hash,
        "proof_hash": proof_hash,
        "policy_version": POLICY_VERSION,
        "ts": ts,
    }
