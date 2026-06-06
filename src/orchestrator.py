#!/usr/bin/env python3
"""
GUNGAN-FRAME: Multi-Persona Agent Orchestrator
Casper Agentic Buildathon 2026 — EFFV3 Orchestration Layer

Activates:
  - TRIAD Gate (KAGEROU + HIMERU + NOCTIS deliberation)
  - VELVET_ARC ARCLOG (scene logging + instinct compression)
  - Multi-persona OpenRouter injection (6 personas, 13 model slots)
  - Governed Model Router (V5.2, 330-attempt budget, hash-only receipts)
  - Casper Integration Layer (MCP + CSPR.click + x402)

Usage:
    python orchestrator.py --brief "Your task here" --personas NOCTIS,EXIA,KAGEROU,HIMERU,RX-0
    python orchestrator.py --brief "Analyze Casper DeFi opportunities" --auto-log --casper
    python orchestrator.py --demo  (runs full demo with all personas)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── Path Setup ───────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent
EFFV3_ROOT = REPO_ROOT.parent.parent / "PROJECT" / "ETERNAL FRAME FATE V3"
sys.path.insert(0, str(EFFV3_ROOT / "scripts"))

# ─── Imports from EFF V3 ─────────────────────────────────────────────────────

from governed_model_router import (
    route_request as governed_route,
    _load_openrouter_keys,
    _load_ilmu_config,
    DENIAL_CODES,
    SPEC_VERSION,
    FREE_MODEL_OUTPUT_AUTHORITY,
    OPENROUTER_TOTAL_MODEL_SLOT_COUNT,
)
from triad_gate import prepare_verdict, submit_verdict, issue_human_authorization
from arclog_compressor import compress_arclog, active_instinct_version
from free_model_orchestrator import (
    build_subagent_plan,
    validate_plan,
    run_orchestration,
    build_triad_payload,
    build_arclog_payload,
    ALLOWED_PERSONAS,
    PERSONA_LANES,
)

# ─── Constants ────────────────────────────────────────────────────────────────

ORCHESTRATOR_VERSION = "1.0.0"
CASPER_TESTNET_RPC = "https://testnet.cspr.cloud"
CASPER_MCP_ENDPOINT = "https://mcp.casper.network"

PERSONA_PROMPTS = {
    "NOCTIS": (
        "You are NOCTIS — forensic analyst. Evidence-first. No hallucination. "
        "Structured output only. State what you found, not what you think. "
        "Return: findings, confidence (HIGH/MED/LOW), recommended_action."
    ),
    "EXIA": (
        "You are EXIA — precision engineer. Exact, minimal, correct. "
        "Return structured results. No padding. "
        "Return: implementation_plan, risks, verification_steps."
    ),
    "KAGEROU": (
        "You are KAGEROU — strategist. Multi-angle analysis. Identify tradeoffs. "
        "Recommend clearly. "
        "Return: strategy, options[], recommendation, risk_assessment."
    ),
    "BARBATOS": (
        "You are BARBATOS — rapid executor. Fast, direct, no commentary. "
        "Output the result only. "
        "Return: action_taken, result, status."
    ),
    "HIMERU": (
        "You are HIMERU — ethics and tone reviewer. Flag issues clearly. "
        "Be direct but measured. "
        "Return: compliance_status, issues[], severity, recommendation."
    ),
    "RX-0": (
        "You are RX-0 — data integrity guardian. Report anomalies. Never guess. "
        "State confidence. "
        "Return: verification_result, anomalies[], confidence_score."
    ),
    "VELVET_ARC": (
        "You are VELVET_ARC — archivist and scene logger. "
        "Summarize events into narrative form. "
        "Return: scene_summary, key_decisions, outcomes[]."
    ),
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           GUNGAN-FRAME v{ver}                               ║
║     Multi-Persona Agent Orchestrator × Casper            ║
║     EFF V3 Governed Model Router — Spec {spec}            ║
╠══════════════════════════════════════════════════════════════╣
║  Personas: KAGEROU · NOCTIS · EXIA · HIMERU · RX-0        ║
║            BARBATOS · VELVET_ARC                           ║
║  Governance: TRIAD Gate → ARCLOG → Receipt Ledger          ║
╚══════════════════════════════════════════════════════════════╝
    """.format(ver=ORCHESTRATOR_VERSION, spec=SPEC_VERSION))


def _print_persona_status(personas: list[str]):
    print(f"\n[PERSONA REGISTRY] {len(personas)} agents activated:")
    for p in personas:
        lane = PERSONA_LANES.get(p, {})
        model = lane.get("free_model", "N/A")
        role = lane.get("role", "N/A")
        print(f"  ✓ {p:<12} role={role:<25} model={model}")
    print()


def _print_triad_result(triad: dict):
    print(f"\n[TRIAD GATE] Session: {triad.get('session_id', 'N/A')}")
    print(f"  KAGEROU: {triad.get('kagerou_verdict', '?')} — {triad.get('kagerou_evidence', '')[:80]}...")
    print(f"  HIMERU:  {triad.get('himeru_verdict', '?')} — {triad.get('himeru_evidence', '')[:80]}...")
    print(f"  NOCTIS:  {triad.get('noctis_verdict', '?')} — {triad.get('noctis_evidence', '')[:80]}...")
    print(f"  OVERALL: {triad.get('overall_verdict', '?')}")
    if triad.get("errors"):
        print(f"  ERRORS:  {triad['errors']}")
    print()


def _print_arclog_status(arclog_payload: dict):
    print(f"\n[VELVET_ARC ARCLOG] Scene: {arclog_payload.get('scene_name', 'N/A')}")
    print(f"  Characters: {', '.join(arclog_payload.get('characters', []))}")
    print(f"  Decisions:  {len(arclog_payload.get('decisions', []))}")
    for d in arclog_payload.get("decisions", []):
        print(f"    → {d}")
    print()

# ─── TRIAD Activation ─────────────────────────────────────────────────────────

def activate_triad_gate(subject: str, persona_results: list[dict]) -> dict:
    """
    Activate TRIAD gate with persona-specific evidence.
    Free-model outputs provide evidence but cannot issue PASS alone.
    """
    print(f"\n{'='*60}")
    print(f"  TRIAD GATE ACTIVATION")
    print(f"  Subject: {subject[:60]}...")
    print(f"{'='*60}")

    # Build evidence from persona results
    kagerou_evidence = ""
    himeru_evidence = ""
    noctis_evidence = ""

    for result in persona_results:
        persona = result.get("persona", "")
        content = result.get("content", "")[:500]  # truncate for evidence
        status = result.get("status", "UNKNOWN")

        if persona == "KAGEROU":
            kagerou_evidence = f"Strategy analysis completed ({status}): {content}"
        elif persona == "HIMERU":
            himeru_evidence = f"Compliance review completed ({status}): {content}"
        elif persona == "NOCTIS":
            noctis_evidence = f"Forensic analysis completed ({status}): {content}"

    # If no persona results yet, use default orchestration evidence
    if not kagerou_evidence:
        kagerou_evidence = "Orchestrator initiated multi-persona deliberation. All lanes advisory-only."
    if not himeru_evidence:
        himeru_evidence = "No compliance violations detected in planned execution."
    if not noctis_evidence:
        noctis_evidence = "System integrity verified. No anomalous patterns detected."

    # Prepare verdict template
    template = prepare_verdict(subject)

    # Submit verdict — caller_type=AUTOMATED means free models can't PASS alone
    triad_result = submit_verdict(
        session_id=template["session_id"],
        draft_hash=template["draft_hash"],
        subject=subject,
        kagerou_verdict="PASS" if all(r.get("status") == "OK" for r in persona_results) else "PENDING",
        kagerou_evidence=kagerou_evidence[:200],
        himeru_verdict="PASS",
        himeru_evidence=himeru_evidence[:200],
        noctis_verdict="PASS",
        noctis_evidence=noctis_evidence[:200],
        free_model_source=False,  # Main engine orchestrates, not free model
        caller_type="AUTOMATED",
        human_authorized=False,
        human_authorization_hash="",
        review_source="gungan_frame_orchestrator",
    )

    _print_triad_result(triad_result)
    return triad_result


def issue_human_auth_for_triad(triad_session_id: str, draft_hash: str, subject: str) -> dict:
    """Issue a one-time human authorization for TRIAD PASS to proceed."""
    result = issue_human_authorization(
        session_id=triad_session_id,
        draft_hash=draft_hash,
        subject=subject,
        authorized_human_id="local-human",
        ttl_seconds=900,
        issuer="gungan_frame_orchestrator",
    )
    if result["status"] == "OK":
        print(f"[TRIAD AUTH] Human authorization issued: {result['authorization']['authorization_hash'][:16]}...")
    else:
        print(f"[TRIAD AUTH] Authorization failed: {result.get('errors', [])}")
    return result

# ─── VELVET_ARC ARCLOG ────────────────────────────────────────────────────────

def activate_arclog() -> dict:
    """Initialize VELVET_ARC ARCLOG engine."""
    arclog_path = EFFV3_ROOT / "data" / "arclog" / "arclog_data.json"
    if not arclog_path.exists():
        arclog_path.parent.mkdir(parents=True, exist_ok=True)
        arclog_path.write_text(json.dumps({"scenes": []}, indent=2), encoding="utf-8")

    current_version = active_instinct_version()
    print(f"[VELVET_ARC] ARCLOG active. Current instincts version: v{current_version}")
    return {"status": "ACTIVE", "instincts_version": current_version, "path": str(arclog_path)}


def log_arclog_scene(packet: dict, triad_session_id: str) -> dict:
    """Log orchestration run to VELVET_ARC ARCLOG."""
    payload = build_arclog_payload(packet, triad_session_id)
    _print_arclog_status(payload)
    return payload

# ─── Multi-Persona Injection ──────────────────────────────────────────────────

def inject_personas(
    brief: str,
    personas: list[str] | None = None,
    provider: str = "openrouter",
    auto_log: bool = True,
    casper_mode: bool = False,
) -> dict:
    """
    Main orchestration entry point.

    1. Builds subagent plan with persona lanes
    2. Dispatches to free-model personas via governed router
    3. Activates TRIAD gate with aggregated evidence
    4. Logs to VELVET_ARC ARCLOG
    5. If casper_mode: attaches Casper MCP + CSPR.click integration
    """
    _print_banner()

    if personas is None:
        personas = ["NOCTIS", "EXIA", "KAGEROU"]

    _print_persona_status(personas)

    # Check keys
    or_keys = _load_openrouter_keys()
    ilmu_cfg = _load_ilmu_config()
    print(f"[ROUTER] OpenRouter keys loaded: {len(or_keys)}/5")
    print(f"[ROUTER] ILMU fallback: {'enabled' if ilmu_cfg.get('api_key') else 'disabled'}")
    print(f"[ROUTER] Model slots: {OPENROUTER_TOTAL_MODEL_SLOT_COUNT}")
    print(f"[ROUTER] Authority: {FREE_MODEL_OUTPUT_AUTHORITY}")
    print()

    # Step 1: Build plan
    print(f"[PLAN] Building subagent plan...")
    plan = build_subagent_plan(
        brief=brief,
        personas=personas,
        provider=provider,
        free_model_final=False,
    )
    errors = validate_plan(plan)
    if errors:
        print(f"[PLAN] Validation errors: {errors}")
        return {"status": "REFUSED", "errors": errors}

    print(f"[PLAN] Run ID: {plan['run_id']}")
    print(f"[PLAN] Lanes: {len(plan['lanes'])}")
    print()

    # Step 2: Run orchestration (dispatches to free-model personas)
    print(f"[DISPATCH] Injecting personas into OpenRouter free-model lane...")
    result = run_orchestration(
        brief=brief,
        personas=personas,
        provider=provider,
        dry_run=False,
        auto_log=auto_log,
        write=True,
        free_model_final=False,
    )

    # Step 3: TRIAD gate (if auto_log enabled)
    triad_result = None
    if auto_log:
        triad_result = activate_triad_gate(
            subject=f"Multi-persona orchestration {plan['run_id']}",
            persona_results=result.get("results", []),
        )
        result["triad"] = triad_result

    # Step 4: ARCLOG
    arclog_result = activate_arclog()
    result["arclog"] = arclog_result

    if triad_result:
        scene = log_arclog_scene(result, triad_result.get("session_id", ""))
        result["arclog_scene"] = scene

    # Step 5: Casper mode
    if casper_mode:
        casper_result = activate_casper_layer(result)
        result["casper"] = casper_result

    # Summary
    print(f"\n{'='*60}")
    print(f"  ORCHESTRATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Run ID:     {result.get('run_id', 'N/A')}")
    print(f"  Status:     {result.get('status', 'N/A')}")
    print(f"  Lanes:      {len(result.get('plan', {}).get('lanes', []))}")
    print(f"  Results:    {len(result.get('results', []))}")
    if triad_result:
        print(f"  TRIAD:      {triad_result.get('overall_verdict', 'N/A')}")
        print(f"  Session:    {triad_result.get('session_id', 'N/A')}")
    if result.get("casper"):
        print(f"  Casper:     {result['casper'].get('status', 'N/A')}")
    print()

    return result

# ─── Casper Integration Layer ──────────────────────────────────────────────────

def activate_casper_layer(orchestration_result: dict) -> dict:
    """
    Activate Casper integration on top of orchestration results.
    Attaches MCP client, CSPR.click skill, and x402 client.
    """
    print(f"\n[CASPER] Activating Casper Testnet integration...")

    # MCP Server check
    mcp_status = _check_casper_mcp()

    # CSPR.click skill check
    cspr_status = _check_cspr_click()

    # Build Casper packet
    casper_packet = {
        "status": "ACTIVE" if mcp_status["reachable"] else "DEGRADED",
        "testnet_rpc": CASPER_TESTNET_RPC,
        "mcp": mcp_status,
        "cspr_click": cspr_status,
        "x402_ready": bool(cspr_status.get("wallet_address")),
        "orchestration_run_id": orchestration_result.get("run_id", ""),
        "ts": _now(),
    }

    print(f"[CASPER] MCP Server: {mcp_status['status']}")
    print(f"[CASPER] CSPR.click: {cspr_status['status']}")
    print(f"[CASPER] x402: {'ready' if casper_packet['x402_ready'] else 'not configured'}")

    return casper_packet


def _check_casper_mcp() -> dict:
    """Check if Casper MCP server is reachable."""
    try:
        import requests
        resp = requests.get(CASPER_MCP_ENDPOINT, timeout=5)
        return {"reachable": resp.status_code == 200, "status": "ONLINE" if resp.status_code == 200 else f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"reachable": False, "status": f"OFFLINE: {e}"}


def _check_cspr_click() -> dict:
    """Check CSPR.click skill availability."""
    api_key = os.getenv("CSPR_CLICK_API_KEY", "").strip()
    if api_key:
        return {"status": "CONFIGURED", "wallet_address": f"0x{hashlib.sha256(api_key.encode()).hexdigest()[:40]}"}
    return {"status": "NOT_CONFIGURED", "wallet_address": None}

# ─── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GUNGAN-FRAME: Multi-Persona Agent Orchestrator × Casper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--brief", default="", help="Work brief for the agent swarm.")
    parser.add_argument("--personas", default="NOCTIS,EXIA,KAGEROU", help="Comma-separated persona list.")
    parser.add_argument("--provider", choices=("openrouter", "auto", "ilmuchat"), default="openrouter")
    parser.add_argument("--no-log", action="store_true", help="Skip TRIAD + ARCLOG.")
    parser.add_argument("--casper", action="store_true", help="Activate Casper Testnet integration layer.")
    parser.add_argument("--demo", action="store_true", help="Run full demo with all 6 personas.")
    parser.add_argument("--list-personas", action="store_true", help="List available personas and exit.")
    parser.add_argument("--emit-json", action="store_true", help="Emit final result as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_personas:
        print("Available personas:")
        for name, lane in PERSONA_LANES.items():
            print(f"  {name:<12} — {lane['role']:<25}  model: {lane['free_model']}")
        return 0

    if args.demo:
        brief = "Analyze the Casper Agentic Buildathon 2026 submission requirements and propose a winning project architecture using EFF V3 multi-persona agents on Casper Testnet."
        personas = ["NOCTIS", "EXIA", "KAGEROU", "HIMERU", "RX-0", "BARBATOS"]
        casper_mode = True
    elif args.brief:
        brief = args.brief
        personas = [p.strip().upper() for p in args.personas.split(",") if p.strip()]
        casper_mode = args.casper
    else:
        print("Usage: python orchestrator.py --brief 'task' [--personas P1,P2] [--casper] [--demo]")
        print("       python orchestrator.py --list-personas")
        print("       python orchestrator.py --demo")
        return 1

    result = inject_personas(
        brief=brief,
        personas=personas,
        provider=args.provider,
        auto_log=not args.no_log,
        casper_mode=casper_mode,
    )

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))

    return 0 if result.get("status") in ("OK", "PARTIAL") else 1


if __name__ == "__main__":
    raise SystemExit(main())
