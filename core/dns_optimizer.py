import time
import re
import socket
import threading
import subprocess
import ipaddress
from typing import Dict, List, Any, Optional
import dns.resolver

DNS_TARGETS = [
    {
        "name": "Cloudflare",
        "primary": "1.1.1.1",
        "secondary": "1.0.0.1",
        "description": "Privacy-focused, ultra-low latency anycast",
        "tag": "Fastest Global"
    },
    {
        "name": "Google Public DNS",
        "primary": "8.8.8.8",
        "secondary": "8.8.4.4",
        "description": "High reliability, global CDN peering",
        "tag": "High Reliability"
    },
    {
        "name": "Quad9",
        "primary": "9.9.9.9",
        "secondary": "149.112.112.112",
        "description": "Built-in threat intelligence & malware blocking",
        "tag": "Secure / Clean"
    },
    {
        "name": "OpenDNS (Cisco)",
        "primary": "208.67.222.222",
        "secondary": "208.67.220.220",
        "description": "Enterprise-grade filtering & stability",
        "tag": "Enterprise"
    }
]

BENCHMARK_DOMAINS = [
    "google.com",
    "cloudflare.com",
    "github.com",
    "microsoft.com"
]

def is_valid_domain(domain: str) -> bool:
    if not domain or len(domain) > 253:
        return False
    pattern = r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-_]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-_]{1,63}(?<!-))*\.?$'
    return bool(re.match(pattern, domain))

class DnsCache:
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def query(self, domain: str, upstream_ip: str = "1.1.1.1") -> Dict[str, Any]:
        domain = domain.strip().lower()
        now = time.time()

        if not is_valid_domain(domain):
            return {
                "domain": domain,
                "ips": [],
                "latency_ms": 0.0,
                "from_cache": False,
                "error": "Invalid domain name format."
            }

        try:
            ipaddress.ip_address(upstream_ip)
            safe_upstream = upstream_ip
        except ValueError:
            safe_upstream = "1.1.1.1"

        with self._lock:
            cached = self._cache.get(domain)
            if cached and cached["expires_at"] > now:
                self.hits += 1
                return {
                    "domain": domain,
                    "ips": cached["ips"],
                    "latency_ms": round((time.time() - now) * 1000, 3),
                    "from_cache": True,
                    "ttl_remaining": int(cached["expires_at"] - now)
                }

        self.misses += 1
        t_start = time.time()
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [safe_upstream]
        resolver.timeout = 2.0
        resolver.lifetime = 2.0

        try:
            answers = resolver.resolve(domain, 'A')
            ips = [rdata.address for rdata in answers]
            ttl = min([answers.rrset.ttl if answers.rrset else 300, 300])
            latency_ms = round((time.time() - t_start) * 1000, 2)

            with self._lock:
                if len(self._cache) >= self.max_size:
                    expired = [k for k, v in self._cache.items() if v["expires_at"] <= now]
                    if expired:
                        for k in expired:
                            del self._cache[k]
                    else:
                        oldest_key = next(iter(self._cache))
                        del self._cache[oldest_key]

                self._cache[domain] = {
                    "ips": ips,
                    "expires_at": now + ttl
                }

            return {
                "domain": domain,
                "ips": ips,
                "latency_ms": latency_ms,
                "from_cache": False,
                "ttl_remaining": ttl
            }
        except Exception as e:
            return {
                "domain": domain,
                "ips": [],
                "latency_ms": round((time.time() - t_start) * 1000, 2),
                "from_cache": False,
                "error": "Resolution error"
            }

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            ratio = round((self.hits / total) * 100, 1) if total > 0 else 0.0
            return {
                "cached_entries": len(self._cache),
                "total_queries": total,
                "cache_hits": self.hits,
                "cache_misses": self.misses,
                "hit_ratio_percent": ratio
            }

class DnsOptimizer:
    def __init__(self):
        self.cache = DnsCache()
        self.last_benchmark_results: List[Dict[str, Any]] = []
        self.recommended_dns: Optional[Dict[str, Any]] = None
        self._benchmarking = False

    def benchmark_all(self) -> List[Dict[str, Any]]:
        if self._benchmarking:
            return self.last_benchmark_results

        self._benchmarking = True
        results = []
        threads = []

        def test_target(target):
            latencies = []
            success_count = 0
            res = dns.resolver.Resolver()
            res.nameservers = [target["primary"]]
            res.timeout = 1.5
            res.lifetime = 1.5

            for domain in BENCHMARK_DOMAINS:
                t0 = time.time()
                try:
                    res.resolve(domain, 'A')
                    elapsed_ms = (time.time() - t0) * 1000
                    latencies.append(elapsed_ms)
                    success_count += 1
                except Exception:
                    pass

            if latencies:
                avg_ms = round(sum(latencies) / len(latencies), 1)
                min_ms = round(min(latencies), 1)
                max_ms = round(max(latencies), 1)
            else:
                avg_ms = 999.0
                min_ms = 999.0
                max_ms = 999.0

            results.append({
                "name": target["name"],
                "primary": target["primary"],
                "secondary": target["secondary"],
                "description": target["description"],
                "tag": target["tag"],
                "avg_ms": avg_ms,
                "min_ms": min_ms,
                "max_ms": max_ms,
                "reliability": round((success_count / len(BENCHMARK_DOMAINS)) * 100, 1)
            })

        for t in DNS_TARGETS:
            th = threading.Thread(target=test_target, args=(t,))
            threads.append(th)
            th.start()

        for th in threads:
            th.join(timeout=8.0)

        results.sort(key=lambda x: (x["avg_ms"], -x["reliability"]))
        self.last_benchmark_results = results
        if results:
            self.recommended_dns = results[0]

        self._benchmarking = False
        return results

    def apply_dns_adapter(self, interface_alias: str, primary: str, secondary: str) -> Dict[str, Any]:
        if not re.match(r'^[a-zA-Z0-9 _-]{1,64}$', interface_alias):
            return {"success": False, "message": "Invalid network interface name."}
        try:
            ipaddress.IPv4Address(primary)
            ipaddress.IPv4Address(secondary)
        except ValueError:
            return {"success": False, "message": "Invalid IPv4 address provided for DNS."}

        try:
            proc = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    "& { param($alias, $p1, $p2) Set-DnsClientServerAddress -InterfaceAlias $alias -ServerAddresses @($p1, $p2) }",
                    interface_alias, primary, secondary
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            if proc.returncode == 0:
                return {
                    "success": True,
                    "message": f"Successfully updated DNS for interface '{interface_alias}' to {primary}, {secondary}"
                }
            return {
                "success": False,
                "message": proc.stderr.strip() or "Administrator privileges required to change adapter DNS."
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
