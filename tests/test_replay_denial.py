import os
import json
import uuid
import pytest
from unittest.mock import patch
from src.governed_action_gate import evaluate_action

def test_nonce_replay(tmp_path, monkeypatch):
    os.environ["T3_MOCK"] = "true"
    monkeypatch.setenv("T3_MOCK", "true")

    # Patch the nonce store directory to use a temporary path
    with patch('src.governed_action_gate.NONCE_STORE_DIR', tmp_path):
        nonce = uuid.uuid4().hex

        mock_proof = {
            "agent_id": "mock-agent-001",
            "public_key_hex": "aabbcc" + "0" * 58,
            "signature_hex": "deadbeef" + "0" * 120,
            "challenge_hex": "ff" * 32,
        }

        result1 = evaluate_action({**mock_proof, "nonce": nonce}, "READ_MEMORY")
        assert result1["decision"] == "ALLOW"

        result2 = evaluate_action({**mock_proof, "nonce": nonce}, "LIST_SKILLS")
        assert result2["decision"] == "DENY"
        assert result2["denial_code"] == "NONCE_REPLAYED"