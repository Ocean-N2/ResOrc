"""
Rich-powered terminal UI for the Resilience Orchestrator.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from config.models import (
    AssetStatus, CampaignConfig, NodeConfig, NodeStatus, TargetAsset,
)

console = Console()


def banner() -> None:
    title = Text()
    title.append("+" + "=" * 46 + "+\n", style="bold cyan")
    title.append("|    RESILIENCE  ORCHESTRATOR  v2.1            |\n", style="bold cyan")
    title.append("|    DDoS Simulation & Defence Testing         |\n", style="bold cyan")
    title.append("+" + "=" * 46 + "+", style="bold cyan")
    console.print(Align.center(title))
    console.print()


def targets_table(targets: List[TargetAsset]) -> None:
    tbl = Table(title="Target Assets", show_lines=True)
    tbl.add_column("#", justify="right", style="dim", width=4)
    tbl.add_column("Address", min_width=30)
    tbl.add_column("Type", width=10)
    tbl.add_column("Port", justify="right", width=6)
    tbl.add_column("Status", width=10)
    tbl.add_column("Latency (ms)", justify="right", width=12)
    _ss = {
        AssetStatus.LIVE: "bold green",
        AssetStatus.DEAD: "bold red",
        AssetStatus.UNKNOWN: "bold yellow",
    }
    for i, t in enumerate(targets, 1):
        style = _ss.get(t.status, "")
        tbl.add_row(
            str(i), t.address, t.asset_type, str(t.port),
            Text(t.status.value, style=style),
            f"{t.latency_ms:.1f}" if t.latency_ms else "-",
        )
    console.print(tbl)


def nodes_table(nodes: List[NodeConfig]) -> None:
    tbl = Table(title="Node Fleet", show_lines=True)
    tbl.add_column("Node ID", min_width=14)
    tbl.add_column("Host", min_width=14)
    tbl.add_column("Port", justify="right", width=6)
    tbl.add_column("Role", width=10)
    tbl.add_column("Max Rate (Mbps)", justify="right", width=16)
    tbl.add_column("Status", width=10)
    _ns = {
        NodeStatus.ONLINE: "bold green",
        NodeStatus.OFFLINE: "bold red",
        NodeStatus.BUSY: "bold yellow",
        NodeStatus.ERROR: "bold magenta",
    }
    for n in nodes:
        tbl.add_row(
            n.node_id, n.host, str(n.port), n.role.value,
            f"{n.max_rate_mbps:.0f}",
            Text(n.status.value, style=_ns.get(n.status, "")),
        )
    console.print(tbl)


def campaign_summary(campaign: CampaignConfig) -> None:
    lines = [
        f"[bold]Campaign:[/bold]  {campaign.name}",
        f"[bold]ID:[/bold]        {campaign.campaign_id}",
        f"[bold]Info:[/bold]      {campaign.description}",
        f"[bold]Phases:[/bold]    {len(campaign.phases)}",
        f"[bold]Nodes:[/bold]     {len(campaign.nodes)}",
        f"[bold]Global Max:[/bold] {campaign.global_max_rate_mbps:.0f} Mbps",
        f"[bold]Abort At:[/bold]  {campaign.abort_threshold_mbps:.0f} Mbps",
        "",
    ]
    for p in campaign.phases:
        lines.append(
            f"  * {p.phase_id}  {p.name:<28} "
            f"{p.attack_mode.value:<14} {p.rate.value_str:>10}  "
            f"{p.duration_seconds}s"
        )
    console.print(Panel("\n".join(lines), title="Campaign Summary",
                        border_style="cyan"))


def phase_progress(tick: Dict[str, Any]) -> None:
    elapsed = tick["elapsed"]
    phase_id = tick["phase_id"]
    ramp = tick["ramp_phase"]
    target = tick["target_mbps"]
    actual = tick["actual_mbps"]
    bar_len = 30
    pct = min(1.0, actual / target) if target > 0 else 0
    filled = int(bar_len * pct)
    bar = "X" * filled + "." * (bar_len - filled)
    color = {"ramp_up": "yellow", "steady": "green",
             "ramp_down": "cyan"}.get(ramp, "white")
    console.print(
        f"  [{color}]{phase_id}[/{color}] "
        f"{elapsed:>6.0f}s  "
        f"|{bar}| "
        f"{actual:>8.1f} / {target:>8.1f} Mbps  "
        f"[{ramp}]",
        end="\r",
    )


def phase_result(result: Dict[str, Any]) -> None:
    console.print()
    status = result.get("status", "unknown")
    style = "green" if status == "done" else "red"
    lines = [
        f"[bold]Phase:[/bold]      {result.get('phase_id', '?')} - {result.get('name', '')}",
        f"[bold]Status:[/bold]     [{style}]{status}[/{style}]",
        f"[bold]Duration:[/bold]   {result.get('duration_actual_s', 0):.1f}s",
        f"[bold]Peak TX:[/bold]    {result.get('peak_tx_mbps', 0):.1f} Mbps",
        f"[bold]Avg  TX:[/bold]    {result.get('avg_tx_mbps', 0):.1f} Mbps",
        f"[bold]Samples:[/bold]    {result.get('metrics_count', 0)}",
        f"[bold]Enforcements:[/bold] {result.get('enforcement_events', 0)}",
    ]
    console.print(Panel("\n".join(lines), title="Phase Result",
                        border_style=style))


def enforcement_events(events: list) -> None:
    if not events:
        console.print("[dim]No enforcement events.[/dim]")
        return
    tbl = Table(title="Enforcement Events", show_lines=True)
    tbl.add_column("Timestamp", width=26)
    tbl.add_column("Node", width=14)
    tbl.add_column("Phase", width=12)
    tbl.add_column("Measured (Mbps)", justify="right", width=16)
    tbl.add_column("Limit (Mbps)", justify="right", width=14)
    tbl.add_column("Action", width=18)
    for e in events:
        style = "red" if getattr(e, "action", "") == "abort" else "yellow"
        tbl.add_row(
            str(getattr(e, "timestamp", "")),
            str(getattr(e, "node_id", "")),
            str(getattr(e, "phase_id", "")),
            f"{getattr(e, 'measured_mbps', 0):.1f}",
            f"{getattr(e, 'limit_mbps', 0):.1f}",
            Text(str(getattr(e, "action", "")), style=style),
        )
    console.print(tbl)


def final_report(result: Dict[str, Any]) -> None:
    lines = [
        f"[bold]Campaign:[/bold] {result.get('campaign_id', '')} - {result.get('name', '')}",
        f"[bold]Aborted:[/bold]  {'Yes' if result.get('aborted') else 'No'}",
        f"[bold]Enforcement Events:[/bold] {result.get('total_enforcement_events', 0)}",
        "",
    ]
    for pr in result.get("phase_results", []):
        st = pr.get("status", "?")
        c = "green" if st == "done" else "red"
        lines.append(
            f"  [{c}]>[/{c}] {pr.get('phase_id', '?')}: "
            f"{pr.get('name', '')} - {st} "
            f"(peak {pr.get('peak_tx_mbps', 0):.0f} Mbps)"
        )
    console.print(Panel("\n".join(lines), title="Campaign Report",
                        border_style="bold cyan"))


def interactive_menu() -> int:
    console.print()
    menu = (
        "[bold cyan]--- Menu -----------------------------------[/bold cyan]\n"
        "  [1] Load Campaign YAML\n"
        "  [2] Scan Targets (RTF)\n"
        "  [3] Check Node Health\n"
        "  [4] Run Full Campaign\n"
        "  [5] Run Single Phase\n"
        "  [6] View Audit Log\n"
        "  [7] Generate Report\n"
        "  [8] Exit\n"
    )
    console.print(menu)
    return IntPrompt.ask("Select", default=8)


def prompt(msg: str, default: Optional[str] = None) -> str:
    return Prompt.ask(msg, default=default)
