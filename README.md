
Resilience Orchestrator v2.1

Purpose: An enterprise-grade orchestration framework for authorized, defensive DDoS simulation and resilience testing using distributed traffic-generation agents (TRex and MHDDoS) under strict governance, safety, and audit controls.

1. Architectural Overview
1.1 Design Goals
The Resilience Orchestrator is designed to:

Safely simulate high-volume and multi-vector traffic in controlled, authorized testing scenarios
Coordinate distributed external nodes to emulate realistic, geographically dispersed traffic sources
Provide deterministic control over traffic rate, ramp-up/down, and duration
Enforce hard safety limits (per-node, aggregate, abort thresholds)
Produce auditor-ready evidence (logs, metrics, reports)

Important: This platform is intended only for environments where explicit written authorization exists for testing.




1.2 High-Level Architecture
┌──────────────────────────────┐
│        Operator / CLI        │
│  (main.py, Rich UI, Reports) │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│     Campaign Orchestration   │
│   (CampaignEngine, Governor)│
└───────────────┬──────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
┌──────────────┐  ┌──────────────┐
│  NodeManager │  │ TargetManager│
│ (Fleet Ctrl) │  │ (RTF Parsing)│
└──────┬───────┘  └──────┬───────┘
       │                  │
       ▼                  ▼
┌──────────────┐  ┌──────────────────┐
│  TRex Agent  │  │ MHDDoS Agent(s)  │
│ (STL / ASTF) │  │ (L4 / L7 Tools)  │
└──────────────┘  └──────────────────┘




2. Core Components
2.1 Configuration Layer (config/)
Key Files:

models.py: Canonical data model (campaigns, phases, rates, nodes, metrics)
loader.py: YAML parsing + semantic validation
Why this matters:

Enforces declarative testing (no ad-hoc scripts)
Enables reproducibility and auditability
Key Concepts:

Campaign → collection of ordered Phases
Phase → attack mode + targets + rate + duration + ramp
RateConfig → human-readable rates (800Mbps, 1.5Gbps)


2.2 Target Handling (targets/)
Capabilities:

Parses RTF target lists (commonly used in enterprise scoping docs)
Supports: IPv4 / IPv6
CIDRs
URLs (with ports)
Hostnames
Target Lifecycle:

Load from RTF or list
Validate scope (optional CIDR allow-list)
Liveness checks (ICMP / TCP / HTTP)
Continuous status tracking


2.3 Node & Agent Layer (agents/)
NodeManager

Registers all external nodes
Abstracts controller differences (TRex vs MHDDoS)
Performs health checks
TRexController

Used for high-bandwidth, packet-accurate traffic
Supports: STL (stateless volumetric floods)
ASTF (stateful / application-like flows)
MHDDoSController

Used for distributed, low-cost, high-variance traffic
Suitable for: TCP / SYN floods
HTTP-layer stress
Controlled via thread-based rate approximation

Controllers operate in simulated mode by default for safe testing.




2.4 Orchestration & Safety (engine/, safety/)
RampController

Linear ramp-up
Steady-state hold
Controlled ramp-down
RateGovernor

Per-node enforcement (auto-throttle)
Aggregate enforcement
Abort threshold → immediate shutdown
Safety Controls

ScopeValidator: CIDR-based allow-listing
AuditLogger: append-only JSONL audit trail


3. Deployment Model – Distributed External Nodes
3.1 Reference Deployment Topology
Internet
   │
   ├── Cloud VM (Region A) ── TRex Agent
   ├── Cloud VM (Region B) ── TRex Agent
   ├── VPS / Bare Metal ──── MHDDoS Agent
   ├── VPS / Bare Metal ──── MHDDoS Agent
   │
Target Environment


Principle: External nodes simulate realistic, diverse source IPs while the orchestrator retains centralized control.


3.2 Agent Deployment (Conceptual)

No exploit payloads or attack scripts are included or required here.


Each external node:

Runs one agent role (TRex or MHDDoS)
Is provisioned with: Fixed CPU / NIC limits
Explicit outbound bandwidth caps
Is pre-registered in sample_nodes.yaml
Required Preconditions:

Written authorization from asset owner
Test windows approved
Rate ceilings defined


3.3 Secure Agent Registration
Each node is declared declaratively:
nodes:
  - node_id: trex-01
    host: 10.20.0.11
    port: 4501
    role: trex
    max_rate_mbps: 1000


Why declarative registration matters:

Prevents rogue nodes
Enables enforceable rate ceilings
Simplifies audit review


4. User Guide
4.1 Installation
pip install -r requirements.txt




4.2 Typical Workflow
Step 1: Prepare Campaign

Define phases in YAML
Attach attack modes, targets, rates
Assign nodes per phase
Step 2: Prepare Targets

Use an RTF scope document
Include only authorized assets
Step 3: Validate Configuration
python main.py validate --campaign config/sample_campaign.yaml


Step 4: Dry-Run (Simulated)
python main.py run --campaign config/sample_campaign.yaml --simulate


Step 5: Controlled Execution (Authorized Only)

Disable simulated mode
Monitor enforcement events
Generate reports


4.3 Interactive Mode
python main.py interactive


Provides:

Menu-driven execution
Live phase progress
Audit log review


5. Output & Evidence
5.1 Generated Artifacts

report.json – machine-readable evidence
report.txt – auditor-friendly narrative
audit.jsonl – immutable action log
5.2 What Auditors Look For

Rate ceilings defined & enforced
Abort thresholds
Target scope validation
Explicit phase definitions


6. Security & Governance Best Practices

Always operate in simulate mode first
Never exceed approved rates
Use separate cloud accounts or VPCs for agents
Rotate campaign IDs per engagement
Archive reports with authorization documents


7. Extensibility
Future enhancements typically include:

gRPC-based remote node control
Certificate-based agent authentication
SIEM export of metrics
Chaos-style failure injection


8. Final Note
This orchestrator is intentionally governance-heavy by design. The goal is not merely traffic generation, but defensible, auditable resilience testing aligned with enterprise risk, legal, and compliance expectations.
If you want, I can:

Convert this into an auditor-ready PDF/Word document
Add a deployment hardening appendix
Produce runbooks per role (Operator / Infra / Audit)
