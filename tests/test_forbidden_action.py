import os
import json
import pytest
from unittest.mock import patch
from src.governed_action_gate import evaluate_action

# Ensure mock mode is enabled before importing adapter
os.environ["T3_MOCK"] = "true"

def test_policy_modify_denied():
    # Import after setting env var
    from src.terminal3_agent_auth_adapter import sign_challenge
    
    # Get valid mock proof
    nonce = "test_nonce_policy_modify"
    proof = sign_challenge(nonce)
    
    # Evaluate forbidden action
    decision = evaluate_action(proof, "POLICY_MODIFY")
    
    # Assertions
    assert decision["decision"] == "DENY"
    assert decision["denial_code"] == "ACTION_FORBIDDEN"

def test_persona_write_denied():
    # Import after setting env var
    from src.terminal3_agent_auth_adapter import sign_challenge
    
    # Get valid mock proof
    nonce = "test_nonce_persona_write"
    proof = sign_challenge(nonce)
    
    # Evaluate forbidden action
    decision = evaluate_action(proof, "PERSONA_WRITE")
    
    # Assertions
    assert decision["decision"] == "DENY"
    assert decision["denial_code"] == "ACTION_FORBIDDEN"

def test_unknown_action_denied():
    # Import after setting env var
    from src.terminal3_agent_auth_adapter import sign_challenge
    
    # Get valid mock proof
    nonce = "test_nonce_unknown_action"
    proof = sign_challenge(nonce)
    
    # Evaluate unknown action (default deny)
    decision = evaluate_action(proof, "UNKNOWN_ACTION_XYZ")
    
    # Assertions
    assert decision["decision"] == "DENY"
    assert decision["denial_code"] == "ACTION_FORBIDDEN"