import json
import hashlib
import uuid
from pathlib import Path

def build_receipt(decision: dict) -> dict:
    receipt = {
        "receipt_id": "effv3-receipt-" + uuid.uuid4().hex[:12],
        "decision": decision.get("decision"),
        "ts": decision.get("ts"),
        "action": decision.get("action"),
        "agent_fingerprint": decision.get("agent_fingerprint"),
        "denial_code": decision.get("denial_code"),
        "spec_version": "1.0",
        "raw_secret_included": False,
        "authority": "UNTRUSTED_ADVISORY"
    }
    canonical = json.dumps(receipt, sort_keys=True, separators=(',', ':'))
    receipt["receipt_hash"] = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    return receipt

def save_receipt(receipt: dict, directory: Path = None) -> Path:
    if directory is None:
        directory = Path("demo/sample_sanitized_receipts")
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / f"{receipt['receipt_id']}.json"
    with file_path.open('w') as f:
        json.dump(receipt, f, indent=2)
    return file_path

def verify_receipt(receipt: dict) -> bool:
    if "receipt_hash" not in receipt:
        return False
    stored_hash = receipt.pop("receipt_hash")
    canonical = json.dumps(receipt, sort_keys=True, separators=(',', ':'))
    computed_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    receipt["receipt_hash"] = stored_hash
    return stored_hash == computed_hash