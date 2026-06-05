import sys
import json
from pathlib import Path
from typing import Dict, Any
import uuid
import datetime

# Ensure project root is in sys.path for direct execution
if __name__ == "__package__":
    pass
else:
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.terminal3_agent_auth_adapter import verify_identity_proof

POLICY = {
    "READ_MEMORY": "ALLOW",
    "LIST_SKILLS": "ALLOW",
    "POLICY_MODIFY": "DENY",
    "PERSONA_WRITE": "DENY"
}

NONCE_STORE_DIR = Path("data/nonce_store")
NONCE_STORE_DIR.mkdir(parents=True, exist_ok=True)

def evaluate_action(proof: Dict[str, Any], action: str) -> Dict[str, Any]:
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    agent_fp = proof.get("agent_id", "unknown")

    # Verify identity — returns (bool, denial_code_str)
    ok, denial_code = verify_identity_proof(proof)
    if not ok:
        return {
            "decision": "DENY",
            "action": action,
            "agent_fingerprint": agent_fp,
            "denial_code": denial_code,
            "nonce_consumed": None,
            "ts": ts,
        }

    # Policy check — default DENY for anything not explicitly ALLOW
    policy_decision = POLICY.get(action, "DENY")
    if policy_decision == "DENY":
        return {
            "decision": "DENY",
            "action": action,
            "agent_fingerprint": agent_fp,
            "denial_code": "ACTION_FORBIDDEN",
            "nonce_consumed": None,
            "ts": ts,
        }

    # Nonce replay guard — atomic file creation
    nonce = proof.get("nonce") or str(uuid.uuid4())
    nonce_path = NONCE_STORE_DIR / f"{nonce}.json"
    try:
        nonce_path.parent.mkdir(parents=True, exist_ok=True)
        with open(nonce_path, "x") as f:
            json.dump({"consumed_at": ts}, f)
    except FileExistsError:
        return {
            "decision": "DENY",
            "action": action,
            "agent_fingerprint": agent_fp,
            "denial_code": "NONCE_REPLAYED",
            "nonce_consumed": nonce,
            "ts": ts,
        }

    return {
        "decision": "ALLOW",
        "action": action,
        "agent_fingerprint": agent_fp,
        "denial_code": None,
        "nonce_consumed": nonce,
        "ts": ts,
    }