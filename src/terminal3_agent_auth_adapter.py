import os
import hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

ADAPTER_AUTHORITY = "UNTRUSTED_ADVISORY"

def key_fingerprint(raw_key_hex: str) -> str:
    raw_key_bytes = bytes.fromhex(raw_key_hex)
    to_hash = b"terminal3\x00" + raw_key_bytes
    return hashlib.sha256(to_hash).hexdigest()[:12]

def get_identity() -> dict:
    api_key = os.getenv("TERMINAL3_API_KEY", "")
    if not api_key:
        raise ValueError("TERMINAL3_API_KEY not set")
    
    if api_key.startswith("0x"):
        api_key = api_key[2:]
    
    if len(api_key) != 64:
        raise ValueError("TERMINAL3_API_KEY must be 32 bytes (64 hex chars) after 0x prefix")
    
    try:
        bytes.fromhex(api_key)
    except ValueError:
        raise ValueError("TERMINAL3_API_KEY must be valid hex")
    
    if os.getenv("T3_MOCK", "false").lower() == "true":
        return {
            "agent_id": "mock-agent-001",
            "public_key_hex": "aabbcc" + "0" * 58,  # 64 chars total
            "signed": True
        }
    
    private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(api_key))
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    public_key_hex = public_key_bytes.hex()
    agent_id = key_fingerprint(api_key)
    
    return {
        "agent_id": agent_id,
        "public_key_hex": public_key_hex,
        "signed": True
    }

def sign_challenge(challenge_bytes) -> dict:
    if isinstance(challenge_bytes, str):
        challenge_bytes = challenge_bytes.encode()

    if os.getenv("T3_MOCK", "false").lower() == "true":
        return {
            "agent_id": "mock-agent-001",
            "public_key_hex": "aabbcc" + "0" * 58,
            "signature_hex": "deadbeef" + "0" * 120,
            "challenge_hex": challenge_bytes.hex(),
        }

    api_key = os.getenv("TERMINAL3_API_KEY", "")
    if not api_key:
        raise ValueError("TERMINAL3_API_KEY not set")

    if api_key.startswith("0x"):
        api_key = api_key[2:]
    
    private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(api_key))
    signature = private_key.sign(challenge_bytes)
    signature_hex = signature.hex()
    challenge_hex = challenge_bytes.hex()
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    public_key_hex = public_key_bytes.hex()
    agent_id = key_fingerprint(api_key)
    
    return {
        "agent_id": agent_id,
        "public_key_hex": public_key_hex,
        "signature_hex": signature_hex,
        "challenge_hex": challenge_hex
    }

def verify_identity_proof(proof: dict) -> tuple[bool, str]:
    required_fields = ["agent_id", "public_key_hex", "signature_hex", "challenge_hex"]
    for field in required_fields:
        if field not in proof:
            return (False, "IDENTITY_MISSING")

    if os.getenv("T3_MOCK", "false").lower() == "true":
        return (True, "")

    try:
        public_key_bytes = bytes.fromhex(proof["public_key_hex"])
        if len(public_key_bytes) != 32:
            return (False, "IDENTITY_INVALID")
        signature_bytes = bytes.fromhex(proof["signature_hex"])
        if len(signature_bytes) != 64:
            return (False, "IDENTITY_INVALID")
        challenge_bytes = bytes.fromhex(proof["challenge_hex"])
    except ValueError:
        return (False, "IDENTITY_INVALID")

    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature_bytes, challenge_bytes)
        return (True, "")
    except Exception:
        return (False, "IDENTITY_INVALID")