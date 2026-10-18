import time
import socket
import psutil
import threading
from typing import Dict, List, Any, Optional

class TelemetryEngine:
    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self.last_nic_counters = {}
        self.last_sample_time = time.time()
        self.current_download_rate = 0.0
        self.current_upload_rate = 0.0
        self.total_bytes_recv = 0
        self.total_bytes_sent = 0

        self.active_interface: Dict[str, Any] = {}
        self.process_metrics: List[Dict[str, Any]] = []
        self.socket_connections: List[Dict[str, Any]] = []
        self._proc_io_history: Dict[int, tuple] = {}

    def start(self):
        with self._lock:
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._sampling_loop, daemon=True)
                self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _sampling_loop(self):
        self._sample_network_interfaces()
        while self._running:
            try:
                self._sample_network_interfaces()
                self._sample_processes()
                self._sample_sockets()
            except Exception:
                pass
            time.sleep(self.sample_interval)

    def _sample_network_interfaces(self):
        now = time.time()
        time_delta = max(now - self.last_sample_time, 0.001)

        io_counters = psutil.net_io_counters(pernic=True)
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        primary_iface = None
        max_traffic = -1
        total_recv = 0
        total_sent = 0

        for nic_name, counters in io_counters.items():
            if nic_name in stats and stats[nic_name].isup:
                if "loopback" in nic_name.lower():
                    continue

                total_traffic = counters.bytes_recv + counters.bytes_sent
                if total_traffic > max_traffic:
                    max_traffic = total_traffic
                    primary_iface = nic_name

            total_recv += counters.bytes_recv
            total_sent += counters.bytes_sent

        if self.last_nic_counters:
            prev_recv = sum(c.bytes_recv for c in self.last_nic_counters.values())
            prev_sent = sum(c.bytes_sent for c in self.last_nic_counters.values())
            self.current_download_rate = max(0.0, (total_recv - prev_recv) / time_delta)
            self.current_upload_rate = max(0.0, (total_sent - prev_sent) / time_delta)

        self.total_bytes_recv = total_recv
        self.total_bytes_sent = total_sent
        self.last_nic_counters = io_counters
        self.last_sample_time = now

        if primary_iface:
            ip_address = "127.0.0.1"
            mac_address = "N/A"
            if primary_iface in addrs:
                for snic in addrs[primary_iface]:
                    if snic.family == socket.AF_INET:
                        ip_address = snic.address
                    elif hasattr(psutil, 'AF_LINK') and snic.family == psutil.AF_LINK:
                        raw_mac = snic.address.replace("-", ":").split(":")
                        if len(raw_mac) >= 6:
                            mac_address = f"**:**:**:**:{raw_mac[-2]}:{raw_mac[-1]}"
                        else:
                            mac_address = "Masked"

            nic_stat = stats.get(primary_iface)
            link_speed = f"{nic_stat.speed} Mbps" if nic_stat and nic_stat.speed > 0 else "Active"

            self.active_interface = {
                "name": primary_iface,
                "ip": ip_address,
                "mac": mac_address,
                "speed": link_speed,
                "status": "Up" if (nic_stat and nic_stat.isup) else "Down"
            }

    def _sample_processes(self):
        now = time.time()
        results = []

        try:
            connections = psutil.net_connections(kind='inet')
        except Exception:
            connections = []

        pids_with_network = set()
        pid_conns_count: Dict[int, int] = {}
        for conn in connections:
            if conn.pid:
                pids_with_network.add(conn.pid)
                pid_conns_count[conn.pid] = pid_conns_count.get(conn.pid, 0) + 1

        active_pids = set()
        for pid in pids_with_network:
            try:
                p = psutil.Process(pid)
                name = p.name()
                active_pids.add(pid)

                io = p.io_counters()
                r_bytes = io.read_bytes
                w_bytes = io.write_bytes

                down_rate = 0.0
                up_rate = 0.0
                if pid in self._proc_io_history:
                    last_r, last_w, last_t = self._proc_io_history[pid]
                    dt = max(now - last_t, 0.001)
                    down_rate = max(0.0, (r_bytes - last_r) / dt)
                    up_rate = max(0.0, (w_bytes - last_w) / dt)

                self._proc_io_history[pid] = (r_bytes, w_bytes, now)
                category = self._classify_application(name)
                priority_nice = p.nice()

                results.append({
                    "pid": pid,
                    "name": name,
                    "category": category,
                    "connections": pid_conns_count.get(pid, 1),
                    "download_rate": down_rate,
                    "upload_rate": up_rate,
                    "priority": priority_nice,
                    "cpu_percent": p.cpu_percent(interval=None),
                    "memory_mb": round(p.memory_info().rss / (1024 * 1024), 1)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        for stale_pid in list(self._proc_io_history.keys()):
            if stale_pid not in active_pids:
                del self._proc_io_history[stale_pid]

        results.sort(key=lambda x: (x["download_rate"] + x["upload_rate"], x["connections"]), reverse=True)
        self.process_metrics = results

    def _sample_sockets(self):
        try:
            conns = psutil.net_connections(kind='inet')
        except Exception:
            return

        active_conns = []
        for c in conns:
            if c.status == 'ESTABLISHED' and c.raddr:
                try:
                    pname = psutil.Process(c.pid).name() if c.pid else "System"
                except Exception:
                    pname = "Unknown"

                active_conns.append({
                    "pid": c.pid,
                    "process": pname,
                    "proto": "TCP" if c.type == socket.SOCK_STREAM else "UDP",
                    "local": f"{c.laddr.ip}:{c.laddr.port}",
                    "remote": f"{c.raddr.ip}:{c.raddr.port}",
                    "status": c.status
                })
            if len(active_conns) >= 50:
                break
        self.socket_connections = active_conns

    def _classify_application(self, name: str) -> str:
        name_lower = name.lower()
        if any(b in name_lower for b in ["chrome", "msedge", "firefox", "brave", "opera", "safari"]):
            return "Web Browser"
        if any(g in name_lower for g in ["steam", "epicgames", "riot", "valorant", "csgo", "dota", "discord", "game"]):
            return "Gaming & Voice"
        if any(c in name_lower for c in ["zoom", "teams", "slack", "webex", "skype", "telegram"]):
            return "Collaboration"
        if any(d in name_lower for d in ["torrent", "qbittorrent", "idm", "download", "onedrive", "dropbox"]):
            return "Bulk Transfer"
        if any(s in name_lower for s in ["svchost", "system", "services", "taskhost"]):
            return "OS Service"
        return "Application"

    def get_snapshot(self) -> Dict[str, Any]:
        return {
            "timestamp": time.time(),
            "adapter": self.active_interface,
            "rates": {
                "download_bps": self.current_download_rate,
                "upload_bps": self.current_upload_rate,
                "download_kbps": round(self.current_download_rate / 1024, 2),
                "upload_kbps": round(self.current_upload_rate / 1024, 2),
                "download_mbps": round((self.current_download_rate * 8) / (1024 * 1024), 2),
                "upload_mbps": round((self.current_upload_rate * 8) / (1024 * 1024), 2),
                "total_recv_mb": round(self.total_bytes_recv / (1024 * 1024), 1),
                "total_sent_mb": round(self.total_bytes_sent / (1024 * 1024), 1),
            },
            "top_processes": self.process_metrics[:15],
            "connections_count": len(self.socket_connections),
            "recent_sockets": self.socket_connections[:12]
        }
