#!/usr/bin/env python3
"""
Resilience Orchestrator - CLI entry point.

Usage:
    python main.py run --campaign config/sample_campaign.yaml --simulate
    python main.py scan --targets config/sample_targets.rtf
    python main.py nodes --config config/sample_nodes.yaml
    python main.py validate --campaign config/sample_campaign.yaml
    python main.py interactive
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.loader import load_campaign, load_nodes, validate_campaign
from targets.manager import TargetManager
from agents.node_manager import NodeManager
from engine.campaign_engine import CampaignEngine
from safety.audit_logger import AuditLogger
from display import dashboard as ui
from display import report as rpt


def _resolve(path: str) -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(path):
        path = os.path.join(base, path)
    return path


def cmd_run(args: argparse.Namespace) -> None:
    campaign = load_campaign(_resolve(args.campaign))
    nm = NodeManager(simulate=args.simulate)
    nm.register_all(campaign.nodes)
    tm = TargetManager()
    if args.targets:
        tm.load_from_rtf(_resolve(args.targets))
    engine = CampaignEngine(campaign, nm, tm, simulate=args.simulate)
    audit = AuditLogger(log_path=_resolve("audit.jsonl"))
    ui.banner()
    ui.campaign_summary(campaign)
    ui.nodes_table(campaign.nodes)
    if tm.targets:
        ui.targets_table(tm.targets)
    phase_sel = args.phases.split(",") if args.phases else None
    audit.log_action("cli", "campaign_start",
                     f"Starting campaign {campaign.campaign_id}", phase_id="*")

    def on_tick(tick):
        ui.phase_progress(tick)

    result = asyncio.run(
        engine.run_campaign(phase_selector=phase_sel, on_tick=on_tick))
    ui.console.print()
    for pr in result.get("phase_results", []):
        ui.phase_result(pr)
    ui.enforcement_events(engine.governor.enforcement_log)
    ui.final_report(result)
    json_path = rpt.generate_json_report(result, _resolve("report.json"))
    txt_path = rpt.generate_text_report(result, _resolve("report.txt"))
    ui.console.print(f"\n[dim]Reports saved: {json_path}, {txt_path}[/dim]")
    audit.log_action("cli", "campaign_end",
                     f"Campaign finished. Aborted={result.get('aborted')}", phase_id="*")


def cmd_scan(args: argparse.Namespace) -> None:
    ui.banner()
    tm = TargetManager()
    count = tm.load_from_rtf(_resolve(args.targets))
    ui.console.print(f"[bold]{count}[/bold] targets loaded from RTF.")
    ui.targets_table(tm.targets)


def cmd_nodes(args: argparse.Namespace) -> None:
    ui.banner()
    cfg_path = _resolve(args.config)
    try:
        campaign = load_campaign(cfg_path)
        nodes = campaign.nodes
    except Exception:
        nodes = load_nodes(cfg_path)
    nm = NodeManager(simulate=True)
    nm.register_all(nodes)
    health = nm.check_health_all()
    ui.nodes_table(nm.all_nodes)
    for nid, ok in health.items():
        status = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
        ui.console.print(f"  {nid}: {status}")


def cmd_validate(args: argparse.Namespace) -> None:
    ui.banner()
    campaign = load_campaign(_resolve(args.campaign))
    warnings = validate_campaign(campaign)
    ui.campaign_summary(campaign)
    if warnings:
        ui.console.print("[bold yellow]Warnings:[/bold yellow]")
        for w in warnings:
            ui.console.print(f"  !  {w}")
    else:
        ui.console.print("[bold green]Campaign configuration is valid.[/bold green]")


def cmd_interactive(_args: argparse.Namespace) -> None:
    ui.banner()
    campaign = None
    tm = TargetManager()
    nm = NodeManager(simulate=True)
    audit = AuditLogger(log_path=_resolve("audit.jsonl"))

    while True:
        choice = ui.interactive_menu()
        if choice == 1:
            path = ui.prompt("Campaign YAML path",
                             default="config/sample_campaign.yaml")
            try:
                campaign = load_campaign(_resolve(path))
                nm = NodeManager(simulate=True)
                nm.register_all(campaign.nodes)
                ui.campaign_summary(campaign)
                audit.log_action("user", "load_campaign", path)
            except Exception as exc:
                ui.console.print(f"[red]Error: {exc}[/red]")
        elif choice == 2:
            path = ui.prompt("Targets RTF path",
                             default="config/sample_targets.rtf")
            try:
                count = tm.load_from_rtf(_resolve(path))
                ui.console.print(f"[bold]{count}[/bold] targets loaded.")
                ui.targets_table(tm.targets)
            except Exception as exc:
                ui.console.print(f"[red]Error: {exc}[/red]")
        elif choice == 3:
            if not nm.all_nodes:
                ui.console.print("[yellow]Load a campaign first.[/yellow]")
                continue
            nm.check_health_all()
            ui.nodes_table(nm.all_nodes)
        elif choice == 4:
            if campaign is None:
                ui.console.print("[yellow]Load a campaign first.[/yellow]")
                continue
            engine = CampaignEngine(campaign, nm, tm, simulate=True)
            result = asyncio.run(engine.run_campaign(
                on_tick=lambda t: ui.phase_progress(t)))
            ui.console.print()
            for pr in result.get("phase_results", []):
                ui.phase_result(pr)
            ui.final_report(result)
        elif choice == 5:
            if campaign is None:
                ui.console.print("[yellow]Load a campaign first.[/yellow]")
                continue
            pid = ui.prompt("Phase ID to run")
            engine = CampaignEngine(campaign, nm, tm, simulate=True)
            result = asyncio.run(engine.run_campaign(phase_selector=[pid]))
            ui.console.print()
            for pr in result.get("phase_results", []):
                ui.phase_result(pr)
        elif choice == 6:
            try:
                entries = audit.get_entries()
                for e in entries:
                    ui.console.print(
                        f"  {e.timestamp}  {e.actor:<8} {e.action:<20} {e.detail}")
            except Exception as exc:
                ui.console.print(f"[red]{exc}[/red]")
        elif choice == 7:
            ui.console.print("[dim]Run a campaign first to generate reports.[/dim]")
        elif choice == 8:
            ui.console.print("[bold]Goodbye.[/bold]")
            break


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resilience-orch",
        description="Resilience Orchestrator - DDoS simulation & defence testing",
    )
    sub = parser.add_subparsers(dest="command")
    p_run = sub.add_parser("run", help="Execute a campaign")
    p_run.add_argument("--campaign", required=True)
    p_run.add_argument("--targets", help="RTF target list (optional)")
    p_run.add_argument("--simulate", action="store_true", default=True)
    p_run.add_argument("--no-simulate", dest="simulate", action="store_false")
    p_run.add_argument("--phases", help="Comma-separated phase IDs")
    p_scan = sub.add_parser("scan", help="Scan targets from RTF")
    p_scan.add_argument("--targets", required=True)
    p_nodes = sub.add_parser("nodes", help="Check node fleet health")
    p_nodes.add_argument("--config", required=True)
    p_val = sub.add_parser("validate", help="Validate campaign config")
    p_val.add_argument("--campaign", required=True)
    sub.add_parser("interactive", help="Interactive menu mode")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {
        "run": cmd_run, "scan": cmd_scan, "nodes": cmd_nodes,
        "validate": cmd_validate, "interactive": cmd_interactive,
    }
    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        cmd_interactive(args)


if __name__ == "__main__":
    main()
