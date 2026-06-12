"""
SmallEffv3 — Python bridge client for the TypeScript T3N SDK layer.

Replaces the old local Ed25519 signing path.
The TypeScript bridge (t3n-bridge/) handles all real T3N operations:
  - Real handshake() + authenticate() → verified DID
  - Real buildDelegationCredential() + signCredential()
  - Real buildInvocationPreimage() + signAgentInvocation()
  - Real revokeDelegation()
  - Real executeAndDecode() for TEE contract invocations

This module spawns the TypeScript bridge as a subprocess and parses its
JSON output for use in the Python governance layer.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BRIDGE_DIR = Path(__file__).parent.parent / "t3n-bridge"
BRIDGE_ENTRY = BRIDGE_DIR / "src" / "index.ts"


def _api_key() -> str:
    key = os.getenv("T3N_API_KEY", "").strip()
    if not key:
        raise ValueError("T3N_API_KEY not set")
    return key


def run_bridge_demo() -> dict:
    """
    Run the full T3N bridge demo and return the summary as a dict.
    Output lines starting with '[+]', '[~]', '[-]' are parsed for key results.
    """
    env = {**os.environ, "T3N_API_KEY": _api_key()}
    result = subprocess.run(
        ["node", "--loader", "ts-node/esm", str(BRIDGE_ENTRY)],
        cwd=str(BRIDGE_DIR),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )

    lines = (result.stdout + result.stderr).splitlines()
    summary = {
        "exit_code": result.returncode,
        "auth_ok": False,
        "did": None,
        "credential_ok": False,
        "vc_id": None,
        "functions": [],
        "envelope_ok": False,
        "tee_ok": False,
        "revocation_attempted": False,
        "raw_lines": lines,
    }

    for line in lines:
        s = line.strip()
        if "handshake() complete" in s and "authenticate() complete" in s:
            summary["auth_ok"] = True
        if "Real DID from session:" in s:
            summary["did"] = s.split("Real DID from session:")[-1].strip()
            summary["auth_ok"] = True
        if "authenticate() complete" in s:
            summary["auth_ok"] = True
        if "Credential built" in s:
            summary["credential_ok"] = True
        if "vc_id" in s and ":" in s and not s.startswith("["):
            # parse "vc_id     : <hex>"
            val = s.split(":")[-1].strip()
            if len(val) == 32:
                summary["vc_id"] = val
        if "functions :" in s:
            summary["functions"] = [f.strip() for f in s.split(":")[-1].split(",")]
        if "DelegationEnvelope built" in s:
            summary["envelope_ok"] = True
        if "TEE invocations  : SUCCESS" in s:
            summary["tee_ok"] = True
        if "revokeDelegation" in s or "Revocation call" in s:
            summary["revocation_attempted"] = True

    return summary


def check_real_identity() -> dict:
    """
    Quick real identity check — auth only, no full demo.
    Returns { did, address, auth_ok }.
    """
    env = {**os.environ, "T3N_API_KEY": _api_key()}
    # Run a minimal script that just auths and prints JSON
    script = """
import { createSession } from './src/auth.js';
const s = await createSession(process.env.T3N_API_KEY);
console.log(JSON.stringify({ did: s.tenantDid, address: s.address, auth_ok: true }));
"""
    result = subprocess.run(
        ["node", "--loader", "ts-node/esm", "--input-type=module", "-e", script],
        cwd=str(BRIDGE_DIR),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )

    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                pass

    return {"did": None, "address": None, "auth_ok": False, "error": result.stderr[-200:]}
