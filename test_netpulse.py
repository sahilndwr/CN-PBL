from core.telemetry import TelemetryEngine
from core.dns_optimizer import DnsOptimizer, is_valid_domain
from core.qos_controller import QosController
from core.analyzer import NetworkAnalyzer
from core.report_generator import ReportGenerator
from web.server import app

def test_suite():
    telemetry = TelemetryEngine()
    telemetry._sample_network_interfaces()
    telemetry._sample_processes()
    telemetry._sample_sockets()
    snap = telemetry.get_snapshot()
    assert "adapter" in snap
    assert "rates" in snap

    dns_opt = DnsOptimizer()
    assert is_valid_domain("cloudflare.com")
    assert not is_valid_domain("<script>alert(1)</script>")
    assert not is_valid_domain("a" * 260 + ".com")

    q1 = dns_opt.cache.query("cloudflare.com", "1.1.1.1")
    assert not q1["from_cache"]
    q2 = dns_opt.cache.query("cloudflare.com", "1.1.1.1")
    assert q2["from_cache"]

    bad_q = dns_opt.cache.query("bad; domain", "1.1.1.1")
    assert "error" in bad_q

    qos = QosController()
    res = qos.apply_profile("gaming")
    assert res["success"]

    analyzer = NetworkAnalyzer()
    analyzer._measure_socket_rtt()
    metrics = analyzer.get_metrics()
    assert "bufferbloat_grade" in metrics

    mtu_res = analyzer.test_mtu()
    assert "optimal_mtu" in mtu_res

    rep_gen = ReportGenerator(telemetry, dns_opt, qos, analyzer)
    md = rep_gen.generate_markdown()
    assert len(md) > 100

    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "default-src 'self'" in resp.headers.get("Content-Security-Policy", "")

    bad_dns_resp = client.post(
        "/api/dns/query",
        json={"domain": "<script>alert(1)</script>"},
        headers={"Origin": "http://localhost:5000", "Host": "localhost:5000"}
    )
    assert bad_dns_resp.status_code == 400

    for _ in range(10):
        client.post(
            "/api/qos/apply",
            json={"profile_id": "balanced"},
            headers={"Origin": "http://localhost:5000", "Host": "localhost:5000"}
        )
    rate_resp = client.post(
        "/api/qos/apply",
        json={"profile_id": "balanced"},
        headers={"Origin": "http://localhost:5000", "Host": "localhost:5000"}
    )
    assert rate_resp.status_code == 429
    assert "Retry-After" in rate_resp.headers

    print("All NetPulse tests and security verifications passed.")

if __name__ == "__main__":
    test_suite()
