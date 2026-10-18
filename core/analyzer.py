import time
import socket
import threading
import subprocess
import ipaddress
from typing import Dict, List, Any

TARGET_HOSTS = ["1.1.1.1", "8.8.8.8"]

class NetworkAnalyzer:
    def __init__(self):
        self.current_rtt = 0.0
        self.min_rtt = 0.0
        self.max_rtt = 0.0
        self.jitter = 0.0
        self.packet_loss_percent = 0.0
        self.bufferbloat_grade = "A+"
        self.health_verdict = "Optimal"

        self._recent_rtts: List[float] = []
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._probe_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _probe_loop(self):
        while self._running:
            try:
                self._measure_socket_rtt()
            except Exception:
                pass
            time.sleep(1.5)

    def _measure_socket_rtt(self):
        host = TARGET_HOSTS[0]
        port = 53
        t0 = time.time()
        success = False

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.2)
            s.connect((host, port))
            rtt_ms = (time.time() - t0) * 1000.0
            s.close()
            success = True
        except Exception:
            rtt_ms = 999.0
            success = False

        with self._lock:
            if success:
                self._recent_rtts.append(rtt_ms)
                if len(self._recent_rtts) > 20:
                    self._recent_rtts.pop(0)

                self.current_rtt = round(rtt_ms, 1)
                self.min_rtt = round(min(self._recent_rtts), 1)
                self.max_rtt = round(max(self._recent_rtts), 1)

                if len(self._recent_rtts) >= 2:
                    diffs = [abs(self._recent_rtts[i] - self._recent_rtts[i-1]) for i in range(1, len(self._recent_rtts))]
                    self.jitter = round(sum(diffs) / len(diffs), 1)
                else:
                    self.jitter = 0.0

                self.packet_loss_percent = 0.0
            else:
                self.current_rtt = 999.0
                self.packet_loss_percent = 20.0

            self._calculate_grade()

    def _calculate_grade(self):
        rtt = self.current_rtt
        jitter = self.jitter
        loss = self.packet_loss_percent

        if loss > 5.0 or rtt > 250:
            self.bufferbloat_grade = "F"
            self.health_verdict = "Severe Congestion"
        elif rtt > 120 or jitter > 30:
            self.bufferbloat_grade = "D"
            self.health_verdict = "High Bufferbloat"
        elif rtt > 65 or jitter > 15:
            self.bufferbloat_grade = "C"
            self.health_verdict = "Moderate Delay"
        elif rtt > 35 or jitter > 8:
            self.bufferbloat_grade = "B"
            self.health_verdict = "Good"
        elif rtt > 20 or jitter > 4:
            self.bufferbloat_grade = "A"
            self.health_verdict = "Very Good"
        else:
            self.bufferbloat_grade = "A+"
            self.health_verdict = "Optimal Latency"

    def test_mtu(self, target: str = "8.8.8.8") -> Dict[str, Any]:
        try:
            ipaddress.ip_address(target)
            safe_target = target
        except ValueError:
            safe_target = "8.8.8.8"

        test_sizes = [1500, 1492, 1472, 1400]
        optimal_mtu = 1500

        for payload_size in test_sizes:
            try:
                proc = subprocess.run(
                    ["ping", "-f", "-l", str(payload_size), safe_target, "-n", "1"],
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if "0% loss" in proc.stdout or "Received = 1" in proc.stdout:
                    optimal_mtu = payload_size + 28
                    break
            except Exception:
                pass

        return {
            "tested_target": safe_target,
            "optimal_mtu": min(optimal_mtu, 1500),
            "status": "No fragmentation detected" if optimal_mtu >= 1472 else "MSS Clamping Recommended"
        }

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "current_rtt_ms": self.current_rtt,
                "min_rtt_ms": self.min_rtt,
                "max_rtt_ms": self.max_rtt,
                "jitter_ms": self.jitter,
                "packet_loss_percent": self.packet_loss_percent,
                "bufferbloat_grade": self.bufferbloat_grade,
                "health_verdict": self.health_verdict,
                "history": list(self._recent_rtts)
            }
