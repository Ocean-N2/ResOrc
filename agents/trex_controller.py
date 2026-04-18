"""
TRex traffic-generator controller (STL / ASTF).
When simulate=True all operations are emulated locally.
"""
from __future__ import annotations

import random
import time
from typing import Dict, List

from config.models import NodeConfig, RateConfig


class TrexController:

    def __init__(self, node: NodeConfig, simulate: bool = True) -> None:
        self.node = node
        self.simulate = simulate
        self._running = False
        self._current_mult: float = 0.0
        self._targets: List[str] = []
        self._start_ts: float = 0.0

    def connect(self) -> bool:
        if self.simulate:
            return True
        return False

    def start_stl(self, rate: RateConfig, targets: List[str]) -> bool:
        self._current_mult = rate.to_trex_multiplier()
        self._targets = targets
        self._running = True
        self._start_ts = time.monotonic()
        return True

    def start_astf(self, rate: RateConfig, targets: List[str]) -> bool:
        self._current_mult = rate.to_trex_multiplier()
        self._targets = targets
        self._running = True
        self._start_ts = time.monotonic()
        return True

    def update_rate(self, new_rate: RateConfig) -> bool:
        if not self._running:
            return False
        self._current_mult = new_rate.to_trex_multiplier()
        return True

    def stop(self) -> bool:
        self._running = False
        self._current_mult = 0.0
        return True

    def get_stats(self) -> Dict:
        if not self._running:
            return {"tx_mbps": 0, "rx_mbps": 0, "pps": 0,
                    "cpu_pct": 0, "active_flows": 0}
        link_gbps = 10
        tx = self._current_mult * link_gbps * 1000
        jitter = random.uniform(-0.02, 0.02) * tx
        tx = max(0, tx + jitter)
        return {
            "tx_mbps": round(tx, 2),
            "rx_mbps": round(tx * random.uniform(0.001, 0.01), 2),
            "pps": int(tx * 1000 / 8 * random.uniform(0.9, 1.1)),
            "cpu_pct": round(min(100, tx / self.node.max_rate_mbps * 80
                                 + random.uniform(0, 5)), 1),
            "active_flows": int(tx * random.uniform(50, 200)),
        }

    @property
    def running(self) -> bool:
        return self._running
