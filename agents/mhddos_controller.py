"""
MHDDoS (Layer-4 / Layer-7) controller.
Simulate mode avoids spawning real processes.
"""
from __future__ import annotations

import random
import time
from typing import Dict, List, Optional

from config.models import AttackMode, NodeConfig, RateConfig

METHODS: Dict[AttackMode, str] = {
    AttackMode.TCP_FLOOD: "TCP",
    AttackMode.SYN_FLOOD: "SYN",
    AttackMode.UDP_FLOOD: "UDP",
    AttackMode.HTTP_FLOOD: "GET",
    AttackMode.SLOWLORIS: "SLOW",
    AttackMode.DNS_AMP:   "DNS",
}


class MHDDoSController:

    def __init__(self, node: NodeConfig, simulate: bool = True) -> None:
        self.node = node
        self.simulate = simulate
        self._process = None
        self._running = False
        self._threads: int = 0
        self._method: str = ""
        self._target: str = ""
        self._duration: int = 0
        self._start_ts: float = 0.0

    @staticmethod
    def build_command(method: AttackMode, target: str,
                      threads: int, duration: int) -> List[str]:
        mhddos_method = METHODS.get(method, "TCP")
        return ["python3", "start.py", mhddos_method, target,
                str(threads), str(duration)]

    def start(self, method: AttackMode, targets: List[str],
              rate: RateConfig, duration: int) -> bool:
        self._threads = rate.to_mhddos_threads()
        self._method = METHODS.get(method, "TCP")
        self._target = targets[0] if targets else ""
        self._duration = duration
        self._running = True
        self._start_ts = time.monotonic()
        if not self.simulate:
            import subprocess
            cmd = self.build_command(method, self._target,
                                     self._threads, duration)
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True

    def stop(self) -> bool:
        self._running = False
        if self._process is not None:
            self._process.terminate()
            self._process = None
        return True

    def kill(self) -> bool:
        self._running = False
        if self._process is not None:
            self._process.kill()
            self._process = None
        return True

    def restart_with_threads(self, threads: int) -> bool:
        was_running = self._running
        self.stop()
        if was_running:
            self._threads = threads
            self._running = True
            self._start_ts = time.monotonic()
        return True

    def get_stats(self) -> Dict:
        if not self._running:
            return {"tx_mbps": 0, "rx_mbps": 0, "pps": 0,
                    "cpu_pct": 0, "active_flows": 0}
        tx = self._threads * 0.5 * random.uniform(0.85, 1.15)
        return {
            "tx_mbps": round(tx, 2),
            "rx_mbps": round(tx * random.uniform(0.001, 0.01), 2),
            "pps": int(tx * 1000 / 8 * random.uniform(0.8, 1.2)),
            "cpu_pct": round(min(100, self._threads / 20
                                 + random.uniform(0, 10)), 1),
            "active_flows": self._threads * random.randint(2, 6),
        }

    @property
    def running(self) -> bool:
        return self._running
