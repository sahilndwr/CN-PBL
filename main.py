import os
import sys
import time
import ctypes
import webbrowser
import threading
from rich.console import Console
from rich.panel import Panel
from web.server import app, telemetry, qos

console = Console()

def print_banner(host: str, port: int, is_elevated: bool, adapter_name: str, ip: str):
    title = "[bold orange3]NETPULSE RADAR[/bold orange3] [bold white]— Network Controller & Traffic Intelligence[/bold white]"
    mode_str = "[bold green]Admin Mode (Kernel NetQoS Active)[/bold green]" if is_elevated else "[bold yellow]User Space Mode (Process Priority Active)[/bold yellow]"

    content = f"""[bold]Active Interface:[/bold] [cyan]{adapter_name}[/cyan] ({ip})
[bold]Privilege Status:[/bold] {mode_str}
[bold]Dashboard URL:[/bold] [bold underline green]http://{host}:{port}[/bold underline green]
[bold]Telemetry Cadence:[/bold] Server-Sent Events (1000ms stream)
[dim]Press Ctrl+C to terminate.[/dim]"""

    console.print(Panel(content, title=title, border_style="orange3", padding=(1, 2)))

def main():
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        is_admin = False

    time.sleep(0.5)
    adapter = telemetry.active_interface
    adapter_name = adapter.get("name", "Active Interface")
    ip_addr = adapter.get("ip", "127.0.0.1")

    host = os.environ.get("NETPULSE_HOST", "127.0.0.1")
    port = int(os.environ.get("NETPULSE_PORT", "5000"))
    print_banner(host, port, is_admin, adapter_name, ip_addr)

    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(f"http://{host}:{port}")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        app.run(host=host, port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        console.print("\n[bold red]Shutting down NetPulse controller...[/bold red]")
        telemetry.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
