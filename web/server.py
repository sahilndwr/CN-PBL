import os
import re
import json
import time
import ipaddress
import threading
from typing import Dict, Any
from flask import Flask, render_template, jsonify, request, Response, send_from_directory
from core.telemetry import TelemetryEngine
from core.dns_optimizer import DnsOptimizer, is_valid_domain
from core.qos_controller import QosController, QOS_PROFILES
from core.analyzer import NetworkAnalyzer
from core.report_generator import ReportGenerator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024
app.config['SECRET_KEY'] = os.environ.get("NETPULSE_SECRET_KEY", os.urandom(24).hex())

telemetry = TelemetryEngine(sample_interval=1.0)
dns_opt = DnsOptimizer()
qos = QosController()
analyzer = NetworkAnalyzer()
report_gen = ReportGenerator(telemetry, dns_opt, qos, analyzer)

telemetry.start()
analyzer.start()

class RateLimiter:
    def __init__(self):
        self._records: Dict[str, list] = {}
        self._lock = threading.Lock()

    def check(self, key: str, max_requests: int, window: int = 60) -> tuple[bool, int]:
        now = time.time()
        with self._lock:
            if key not in self._records:
                self._records[key] = []
            self._records[key] = [t for t in self._records[key] if t > now - window]
            if len(self._records[key]) >= max_requests:
                retry_after = int(window - (now - self._records[key][0])) + 1
                return False, max(1, retry_after)
            self._records[key].append(now)
            return True, 0

limiter = RateLimiter()
active_streams = 0
stream_lock = threading.Lock()

def get_client_ip() -> str:
    return request.remote_addr or "127.0.0.1"

@app.before_request
def security_filter():
    if request.method in ["POST", "PUT", "DELETE"]:
        host = request.headers.get("Host", "")
        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")

        if origin:
            clean_origin = origin.split("://")[-1]
            if clean_origin != host:
                return jsonify({"error": "Forbidden", "message": "Cross-origin request rejected."}), 403
        elif referer:
            clean_referer = referer.split("://")[-1].split("/")[0]
            if clean_referer != host:
                return jsonify({"error": "Forbidden", "message": "Cross-origin referer mismatch."}), 403

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=()'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self'; "
        "img-src 'self' data:; "
        "frame-ancestors 'none';"
    )
    return response

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad Request", "message": "The request contained invalid parameters."}), 400

@app.errorhandler(403)
def forbidden(e):
    return jsonify({"error": "Forbidden", "message": "Request origin not authorized."}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not Found", "message": "The requested resource does not exist."}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method Not Allowed", "message": "HTTP method is not allowed on this endpoint."}), 405

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"error": "Payload Too Large", "message": "Request entity exceeds maximum allowable size (16KB)."}), 413

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({"error": "Too Many Requests", "message": "Rate limit exceeded. Please wait before retrying."}), 429

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal Server Error", "message": "An internal error occurred."}), 500

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/favicon.ico")
def favicon_ico():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "favicon.ico", mimetype="image/vnd.microsoft.icon")

@app.route("/favicon.svg")
def favicon_svg():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "favicon.svg", mimetype="image/svg+xml")

@app.route("/favicon.png")
def favicon_png():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "favicon.png", mimetype="image/png")

@app.route("/api/status")
def get_status():
    ip = get_client_ip()
    ok, retry = limiter.check(f"{ip}:status", 120, 60)
    if not ok:
        return jsonify({"error": "Too Many Requests", "retry_after": retry}), 429, {"Retry-After": str(retry)}

    snap = telemetry.get_snapshot()
    qos_st = qos.get_status()
    health = analyzer.get_metrics()
    dns_cache_st = dns_opt.cache.get_stats()

    return jsonify({
        "status": "online",
        "timestamp": time.time(),
        "adapter": snap["adapter"],
        "rates": snap["rates"],
        "qos": qos_st,
        "health": health,
        "dns_cache": dns_cache_st
    })

@app.route("/api/telemetry")
def get_telemetry():
    ip = get_client_ip()
    ok, retry = limiter.check(f"{ip}:telemetry", 120, 60)
    if not ok:
        return jsonify({"error": "Too Many Requests", "retry_after": retry}), 429, {"Retry-After": str(retry)}

    snap = telemetry.get_snapshot()
    return jsonify(snap)

@app.route("/api/qos/policies", methods=["GET"])
def get_qos_policies():
    return jsonify(qos.get_status())

@app.route("/api/qos/apply", methods=["POST"])
def apply_qos():
    ip = get_client_ip()
    ok, retry = limiter.check(f"{ip}:qos_apply", 10, 60)
    if not ok:
        return jsonify({"error": "Too Many Requests", "retry_after": retry}), 429, {"Retry-After": str(retry)}

    data = request.get_json(silent=True) or {}
    profile_id = str(data.get("profile_id", "balanced")).strip().lower()

    if profile_id not in QOS_PROFILES:
        return jsonify({"error": "Bad Request", "message": f"Invalid QoS profile. Allowed: {list(QOS_PROFILES.keys())}"}), 400

    result = qos.apply_profile(profile_id)
    return jsonify(result)

@app.route("/api/dns/benchmark", methods=["GET", "POST"])
def run_dns_benchmark():
    ip = get_client_ip()
    ok, retry = limiter.check(f"{ip}:dns_benchmark", 10, 60)
    if not ok:
        return jsonify({"error": "Too Many Requests", "retry_after": retry}), 429, {"Retry-After": str(retry)}

    results = dns_opt.benchmark_all()
    return jsonify({
        "results": results,
        "recommended": dns_opt.recommended_dns
    })

@app.route("/api/dns/query", methods=["POST"])
def dns_test_query():
    ip = get_client_ip()
    ok, retry = limiter.check(f"{ip}:dns_query", 30, 60)
    if not ok:
        return jsonify({"error": "Too Many Requests", "retry_after": retry}), 429, {"Retry-After": str(retry)}

    data = request.get_json(silent=True) or {}
    domain = str(data.get("domain", "cloudflare.com")).strip().lower()
    upstream = str(data.get("upstream", "1.1.1.1")).strip()

    if not is_valid_domain(domain):
        return jsonify({"error": "Bad Request", "message": "Invalid domain name syntax."}), 400

    try:
        ipaddress.ip_address(upstream)
    except ValueError:
        return jsonify({"error": "Bad Request", "message": "Invalid upstream DNS resolver IP address."}), 400

    result = dns_opt.cache.query(domain, upstream_ip=upstream)
    result["cache_stats"] = dns_opt.cache.get_stats()
    return jsonify(result)

@app.route("/api/dns/apply", methods=["POST"])
def apply_dns():
    ip = get_client_ip()
    ok, retry = limiter.check(f"{ip}:dns_apply", 10, 60)
    if not ok:
        return jsonify({"error": "Too Many Requests", "retry_after": retry}), 429, {"Retry-After": str(retry)}

    data = request.get_json(silent=True) or {}
    primary = str(data.get("primary", "1.1.1.1")).strip()
    secondary = str(data.get("secondary", "1.0.0.1")).strip()

    try:
        ipaddress.IPv4Address(primary)
        ipaddress.IPv4Address(secondary)
    except ValueError:
        return jsonify({"error": "Bad Request", "message": "Primary and secondary must be valid IPv4 addresses."}), 400

    adapter_name = telemetry.active_interface.get("name", "Wi-Fi")
    res = dns_opt.apply_dns_adapter(adapter_name, primary, secondary)
    return jsonify(res)

@app.route("/api/analyzer/health")
def get_health():
    return jsonify(analyzer.get_metrics())

@app.route("/api/analyzer/mtu", methods=["POST"])
def test_mtu():
    ip = get_client_ip()
    ok, retry = limiter.check(f"{ip}:mtu", 10, 60)
    if not ok:
        return jsonify({"error": "Too Many Requests", "retry_after": retry}), 429, {"Retry-After": str(retry)}

    data = request.get_json(silent=True) or {}
    target = str(data.get("target", "8.8.8.8")).strip()
    try:
        ipaddress.ip_address(target)
    except ValueError:
        target = "8.8.8.8"

    return jsonify(analyzer.test_mtu(target=target))

@app.route("/api/stream")
def stream_metrics():
    global active_streams
    with stream_lock:
        if active_streams >= 5:
            return jsonify({"error": "Too Many Streams", "message": "Concurrent stream limit reached."}), 429
        active_streams += 1

    def generate():
        global active_streams
        try:
            while True:
                snap = telemetry.get_snapshot()
                health = analyzer.get_metrics()
                payload = {
                    "timestamp": time.time(),
                    "rates": snap["rates"],
                    "adapter": snap["adapter"],
                    "top_processes": snap["top_processes"][:10],
                    "health": health,
                    "active_qos": qos.active_profile
                }
                yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(1.0)
        finally:
            with stream_lock:
                active_streams = max(0, active_streams - 1)

    return Response(generate(), mimetype="text/event-stream")

@app.route("/report/print")
def print_report():
    return Response(report_gen.generate_printable_html(), mimetype="text/html")

@app.route("/api/report/markdown")
def download_markdown_report():
    md = report_gen.generate_markdown()
    return Response(
        md,
        mimetype="text/markdown",
        headers={"Content-Disposition": "attachment; filename=netpulse_audit_report.md"}
    )

@app.route("/api/report/preview")
def preview_report():
    return jsonify({
        "markdown": report_gen.generate_markdown()
    })

def create_app():
    return app

if __name__ == "__main__":
    host = os.environ.get("NETPULSE_HOST", "127.0.0.1")
    port = int(os.environ.get("NETPULSE_PORT", "5000"))
    app.run(host=host, port=port, debug=False)
