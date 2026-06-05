import uuid
import os

def test_nonce_replay(tmp_path, monkeypatch):
    monkeypatch.setenv("T3_MOCK", "true")
    import src.governed_action_gate as gate_mod
    monkeypatch.setattr(gate_mod, "NONCE_STORE_DIR", tmp_path)
    
    nonce = uuid.uuid4().hex
    from src.terminal3_agent_auth_adapter import sign_action_request
    
    proof1 = sign_action_request("READ_MEMORY", nonce)
    r1 = gate_mod.evaluate_action(proof1, "READ_MEMORY")
    assert r1["decision"] == "ALLOW"
    
    proof2 = sign_action_request("LIST_SKILLS", nonce)
    r2 = gate_mod.evaluate_action(proof2, "LIST_SKILLS")
    assert r2["decision"] == "DENY"
    assert r2["denial_code"] == "NONCE_REPLAYED"