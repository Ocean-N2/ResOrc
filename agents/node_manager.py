"""
NodeManager – fleet registry and health orchestration.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple, Union

from config.models import NodeConfig, NodeRole, NodeStatus, PhaseConfig
from agents.trex_controller import TrexController
from agents.mhddos_controller import MHDDoSController

Controller = Union[TrexController, MHDDoSController]


class NodeManager:

    def __init__(self, simulate: bool = True) -> None:
        self.simulate = simulate
        self._nodes: Dict[str, NodeConfig] = {}
        self._controllers: Dict[str, Controller] = {}

    def register(self, node: NodeConfig) -> None:
        self._nodes[node.node_id] = node
        if node.role == NodeRole.TREX:
            self._controllers[node.node_id] = TrexController(node, self.simulate)
        else:
            self._controllers[node.node_id] = MHDDoSController(node, self.simulate)

    def register_all(self, nodes: List[NodeConfig]) -> None:
        for n in nodes:
            self.register(n)

    def check_health_all(self) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for nid, ctrl in self._controllers.items():
            ok = ctrl.connect()
            self._nodes[nid].status = (
                NodeStatus.ONLINE if ok else NodeStatus.OFFLINE)
            results[nid] = ok
        return results

    def get_controller(self, node_id: str) -> Controller:
        return self._controllers[node_id]

    def get_node(self, node_id: str) -> NodeConfig:
        return self._nodes[node_id]

    def get_nodes_for_phase(
        self, phase: PhaseConfig
    ) -> List[Tuple[NodeConfig, Controller]]:
        pairs: List[Tuple[NodeConfig, Controller]] = []
        for nid in phase.node_ids:
            if nid in self._nodes:
                pairs.append((self._nodes[nid], self._controllers[nid]))
        return pairs

    def get_all_stats(self) -> Dict[str, Dict]:
        return {nid: ctrl.get_stats()
                for nid, ctrl in self._controllers.items()}

    @property
    def all_nodes(self) -> List[NodeConfig]:
        return list(self._nodes.values())
