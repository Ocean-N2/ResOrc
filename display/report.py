"""
Report generation – JSON and plain-text formats.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

from rich.console import Console

console = Console()


def generate_json_report(campaign_result: Dict[str, Any],
                         path: str = "report.json") -> str:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **campaign_result,
    }
    with open(path, "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    return path


def generate_text_report(campaign_result: Dict[str, Any],
                         path: str = "report.txt") -> str:
    lines: list = []
    lines.append("=" * 60)
    lines.append("RESILIENCE ORCHESTRATOR - CAMPAIGN REPORT")
    lines.append("=" * 60)
    lines.append(f"Generated : {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Campaign  : {campaign_result.get('campaign_id', '')} - "
                 f"{campaign_result.get('name', '')}")
    lines.append(f"Aborted   : {'Yes' if campaign_result.get('aborted') else 'No'}")
    lines.append(f"Enforcements: {campaign_result.get('total_enforcement_events', 0)}")
    lines.append("")
    pf = campaign_result.get("pre_flight", {})
    lines.append("-- Pre-flight --")
    lines.append(f"  Node health : {pf.get('node_health', {})}")
    lines.append(f"  Warnings    : {pf.get('config_warnings', [])}")
    lines.append(f"  Targets     : {pf.get('targets', {})}")
    lines.append(f"  Ready       : {pf.get('ready', False)}")
    lines.append("")
    for pr in campaign_result.get("phase_results", []):
        lines.append(f"-- Phase: {pr.get('phase_id', '?')} - {pr.get('name', '')} --")
        lines.append(f"  Status     : {pr.get('status', '?')}")
        lines.append(f"  Duration   : {pr.get('duration_actual_s', 0):.1f}s")
        lines.append(f"  Peak TX    : {pr.get('peak_tx_mbps', 0):.1f} Mbps")
        lines.append(f"  Avg  TX    : {pr.get('avg_tx_mbps', 0):.1f} Mbps")
        lines.append(f"  Samples    : {pr.get('metrics_count', 0)}")
        lines.append(f"  Enforcements: {pr.get('enforcement_events', 0)}")
        lines.append("")
    lines.append("=" * 60)
    with open(path, "w") as fh:
        fh.write("\n".join(lines))
    return path


def print_summary(campaign_result: Dict[str, Any]) -> None:
    console.print(f"\n[bold]Campaign {campaign_result.get('campaign_id', '')}[/bold]"
                  f" - {campaign_result.get('name', '')}")
    for pr in campaign_result.get("phase_results", []):
        st = pr.get("status", "?")
        icon = "OK" if st == "done" else "FAIL"
        console.print(f"  {icon} {pr.get('phase_id')}: {pr.get('name', '')} "
                      f"- {st} (peak {pr.get('peak_tx_mbps', 0):.0f} Mbps)")
    console.print(f"  Total enforcement events: "
                  f"{campaign_result.get('total_enforcement_events', 0)}")
