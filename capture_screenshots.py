import os
import sys
import time
import subprocess
import urllib.request
from selenium import webdriver
from selenium.webdriver.edge.options import Options

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def wait_for_server(url="http://127.0.0.1:5000", timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    print("Checking if server is running...")
    server_proc = None
    if not wait_for_server(timeout=1):
        print("Starting NetPulse server in background...")
        server_proc = subprocess.Popen(
            [sys.executable, os.path.join(BASE_DIR, "main.py")],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if not wait_for_server(timeout=15):
            print("Failed to start server!")
            if server_proc:
                server_proc.kill()
            sys.exit(1)
        print("Server is up and running at http://127.0.0.1:5000")
    else:
        print("Server is already running.")

    print("Configuring Edge headless driver...")
    edge_opts = Options()
    edge_opts.add_argument("--headless=new")
    edge_opts.add_argument("--window-size=1920,1080")
    edge_opts.add_argument("--disable-gpu")
    edge_opts.add_argument("--no-sandbox")
    edge_opts.add_argument("--hide-scrollbars")
    edge_opts.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    driver = webdriver.Edge(options=edge_opts)
    driver.set_window_size(1920, 1080)

    try:
        print("Navigating to http://127.0.0.1:5000 ...")
        driver.get("http://127.0.0.1:5000")
        print("Waiting for SSE stream and Chart.js to initialize (5s)...")
        time.sleep(5)

        # 1. Radar Overview Dashboard
        p1 = os.path.join(SCREENSHOT_DIR, "01_radar_overview_dashboard.png")
        driver.save_screenshot(p1)
        print(f"[Saved] {p1}")

        # 2. QoS Traffic Controller (Default Balanced)
        driver.execute_script("switchTab(null, 'qos');")
        time.sleep(1.5)
        p2 = os.path.join(SCREENSHOT_DIR, "02_qos_traffic_controller.png")
        driver.save_screenshot(p2)
        print(f"[Saved] {p2}")

        # 3. Apply Gaming Profile & capture with active toast
        driver.execute_script("applyQosProfile('gaming');")
        time.sleep(1.5)
        p3 = os.path.join(SCREENSHOT_DIR, "03_qos_gaming_mode_active.png")
        driver.save_screenshot(p3)
        print(f"[Saved] {p3}")

        # 4. DNS Tab & Run Benchmark & Cache
        driver.execute_script("switchTab(null, 'dns');")
        time.sleep(1.5)
        print("Running DNS benchmark...")
        driver.execute_script("runDnsBenchmark();")
        time.sleep(4.5)

        # Test cache miss then cache hit
        print("Testing DNS cache resolver...")
        driver.execute_script("document.getElementById('dns-test-domain').value = 'cloudflare.com'; testDnsCache();")
        time.sleep(1.5)
        driver.execute_script("testDnsCache();") # Second time for cache hit!
        time.sleep(1.5)
        p4 = os.path.join(SCREENSHOT_DIR, "04_dns_benchmark_and_lru_cache.png")
        driver.save_screenshot(p4)
        print(f"[Saved] {p4}")

        # 5. Bufferbloat & Path MTU Discovery
        driver.execute_script("switchTab(null, 'analyzer');")
        time.sleep(2)
        print("Running Path MTU Discovery...")
        driver.execute_script("runMtuTest();")
        time.sleep(3.5)
        p5 = os.path.join(SCREENSHOT_DIR, "05_bufferbloat_and_path_mtu.png")
        driver.save_screenshot(p5)
        print(f"[Saved] {p5}")

        # 6. Sockets & Process Mapping
        driver.execute_script("switchTab(null, 'sockets');")
        time.sleep(2)
        p6 = os.path.join(SCREENSHOT_DIR, "06_live_socket_process_mapping.png")
        driver.save_screenshot(p6)
        print(f"[Saved] {p6}")

        # 7. Spotlight Command Palette
        driver.execute_script("openSpotlight();")
        time.sleep(1)
        p7 = os.path.join(SCREENSHOT_DIR, "07_spotlight_command_palette.png")
        driver.save_screenshot(p7)
        print(f"[Saved] {p7}")

        # 8. Report Modal Preview
        driver.execute_script("closeSpotlight(); openReportModal();")
        time.sleep(2)
        p8 = os.path.join(SCREENSHOT_DIR, "08_network_audit_report_modal.png")
        driver.save_screenshot(p8)
        print(f"[Saved] {p8}")

        # 9. Printable HTML Audit Report
        driver.get("http://127.0.0.1:5000/report/print")
        time.sleep(2)
        p9 = os.path.join(SCREENSHOT_DIR, "09_printable_html_audit_report.png")
        driver.save_screenshot(p9)
        print(f"[Saved] {p9}")

        print("All screenshots successfully captured!")

    finally:
        driver.quit()
        if server_proc:
            print("Stopping background server...")
            server_proc.kill()

if __name__ == "__main__":
    main()
