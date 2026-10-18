# NetPulse Radar — Comprehensive Project Documentation & Technical Report

> **Endpoint Network Controller & Real-Time Traffic Intelligence Platform**  
> *A non-simulated, kernel-integrated network telemetry, Quality of Service (QoS) controller, DNS benchmarking resolver, and bufferbloat diagnostic engine for Windows.*

---

## Table of Contents
1. [Executive Summary & 30-Second Elevator Pitch](#1-executive-summary--30-second-elevator-pitch)
2. [Problem Statement & Key Innovations](#2-problem-statement--key-innovations)
3. [Comprehensive Technology Stack & Library Justification](#3-comprehensive-technology-stack--library-justification)
4. [OSI Layer Mapping & Theoretical Grounding](#4-osi-layer-mapping--theoretical-grounding)
5. [System Architecture & End-to-End Data Pipeline](#5-system-architecture--end-to-end-data-pipeline)
6. [Visual Tour of Features & Output Verification (Figures 1–9)](#6-visual-tour-of-features--output-verification)
   - [Figure 1: Radar Overview Dashboard](#figure-1-radar-overview-dashboard)
   - [Figure 2: Quality of Service (QoS) Policy Engine](#figure-2-quality-of-service-qos-policy-engine)
   - [Figure 3: Active Gaming Profile & DSCP 46 Enforcement](#figure-3-active-gaming-profile--dscp-46-enforcement)
   - [Figure 4: Upstream DNS Benchmark & Sub-Millisecond Cache](#figure-4-upstream-dns-benchmark--sub-millisecond-cache)
   - [Figure 5: Bufferbloat Jitter Analysis & Path MTU Discovery](#figure-5-bufferbloat-jitter-analysis--path-mtu-discovery)
   - [Figure 6: Live Layer 4 Socket-to-Process Mapping](#figure-6-live-layer-4-socket-to-process-mapping)
   - [Figure 7: Spotlight Command Palette (`Ctrl + K`)](#figure-7-spotlight-command-palette-ctrl--k)
   - [Figure 8: Network Audit Report Generator Modal](#figure-8-network-audit-report-generator-modal)
   - [Figure 9: Print-Ready HTML Network Audit Report](#figure-9-print-ready-html-network-audit-report)
7. [Mathematical Formulations & Algorithmic Foundations](#7-mathematical-formulations--algorithmic-foundations)
8. [Defensive Security Architecture & Threat Defenses](#8-defensive-security-architecture--threat-defenses)
9. [3-Member Presentation Guide & Turn-by-Turn Speaking Scripts](#9-3-member-presentation-guide--turn-by-turn-speaking-scripts)
10. [Viva & Technical Examination Defense Bank (15 Questions)](#10-viva--technical-examination-defense-bank-15-questions)

---

## 1. Executive Summary & 30-Second Elevator Pitch

**NetPulse Radar** is an open-source, production-grade endpoint network controller and traffic optimization platform built for Windows. While traditional academic networking projects rely on synthetic simulators (such as Cisco Packet Tracer or Mininet) that create artificial virtual environments, NetPulse Radar attaches directly to the **live physical Windows network stack** across OSI Layers 3, 4, and 7.

It monitors physical Network Interface Card (NIC) byte deltas in real time, maps every open TCP/UDP socket directly to its originating Process ID (PID), shapes network queues using Windows NetQoS policies and Differentiated Services Code Point (DSCP) packet tagging, benchmarks global recursive DNS resolvers, resolves cached domain lookups from RAM in under **0.05 milliseconds**, and provides real-time link bufferbloat and Path MTU diagnostics on a Cloudflare Radar-inspired obsidian operations console.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        30-SECOND ELEVATOR PITCH                        │
├────────────────────────────────────────────────────────────────────────┤
│ "NetPulse Radar is a live endpoint network controller and traffic      │
│  intelligence platform that operates directly on the Windows network   │
│  stack across OSI Layers 3, 4, and 7. It tracks bandwidth per process  │
│  in real time, controls packet priority using Windows NetQoS and DSCP   │
│  tagging, runs an in-memory sub-millisecond DNS caching resolver,      │
│  and detects bufferbloat and MTU fragmentation—all presented on a      │
│  modern Cloudflare Radar-inspired operations console."                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Problem Statement & Key Innovations

### 2.1 The Limitations of Virtual Simulators
Standard networking curricula predominantly feature tools like Packet Tracer, GNS3, or Mininet. While valuable for conceptual routing demonstrations, simulators suffer from critical limitations:
1. **Zero Operating System Friction:** Packets do not compete with real browser processes, antivirus file scanning, or kernel thread scheduling.
2. **Absence of Real Hardware Contention:** Wi-Fi radio framing, driver packet queue overflow, and router bufferbloat are completely absent.
3. **No Sockets-to-Application Binding:** Students never see how an OS socket actually binds an ephemeral port to an executable binary.

### 2.2 The NetPulse Radar Solution
NetPulse bridges the gap between academic network theory and real-world systems engineering:
* **Direct Hardware Interfacing:** Connects directly to the active physical adapter (Wi-Fi 802.11 / Ethernet 802.3).
* **Process-to-Socket Correlation:** Identifies which local process is communicating with which remote IP address and port, calculating read/write throughput on a per-executable basis.
* **Dual-Tier Traffic Control (QoS):** Combines process-level scheduling priority (`psutil`) with kernel-level packet tagging (`New-NetQosPolicy`).
* **Sub-Millisecond DNS Caching:** Implements an in-memory LRU resolver that eliminates upstream recursive internet round-trips for repeated queries.
* **Objective Bufferbloat Scoring:** Quantifies link quality under active load using RTT jitter variance, giving users an actionable grade (A+ through F).

---

## 3. Comprehensive Technology Stack & Library Justification

| Technology / Component | Version / Spec | Primary Architectural Responsibility | Why Selected Over Alternatives |
| :--- | :--- | :--- | :--- |
| **Python** | 3.9 – 3.13 | Core backend engine, diagnostic probes, and API service. | Fast execution, native low-level socket bindings, robust multiprocessing/threading, clean ctypes integration. |
| **`psutil`** | $\ge 5.9.0$ | OS subsystem telemetry, physical NIC counters, socket tables, process priority adjustment. | Directly queries the Windows kernel; far more efficient and cross-compatible than parsing raw Windows command-line utilities. |
| **`dnspython`** | $\ge 2.3.0$ | Raw DNS packet construction, recursive query benchmarking, TTL inspection. | Complete programmatic control over DNS headers, resolver timeouts, and A-record resolution without OS DNS caching interference. |
| **`Flask`** | $\ge 2.3.0$ | Micro-web framework exposing REST endpoints and the real-time SSE stream. | Minimalist overhead, zero boilerplate ORM bloat, instantaneous cold-start, native streaming response support. |
| **Server-Sent Events (SSE)** | W3C Standard | Unidirectional 1000ms real-time metric streaming from server to client. | Telemetry is strictly one-way (server to client). Unlike WebSockets, SSE requires no protocol upgrade handshakes, handles reconnections natively, and traverses corporate proxies seamlessly. |
| **Windows NetQoS & PowerShell** | Windows 10/11 | Kernel-level packet scheduling and DSCP tagging on the physical network card. | Native Windows API for enterprise packet classification without requiring third-party kernel driver installation. |
| **Chart.js** | 4.4.1 | 60fps HTML5 Canvas time-series throughput visualization. | Hardware-accelerated canvas rendering capable of smoothly plotting rolling 30-second bandwidth windows with zero DOM thrashing. |
| **Vanilla ES6+ JavaScript** | Modern ECMAScript | Frontend event handling, tab routing, spotlight search, DOM updates. | Zero bundlers (no Webpack, Vite, or Node.js runtime required), zero build step, instant deployment, ultra-fast client execution. |
| **Selenium & Headless Edge** | 4.49.0 | Automated end-to-end verification and high-resolution report screenshot capture. | Automates full browser interactions against Microsoft Edge's native Blink engine for production test verification. |

---

## 4. OSI Layer Mapping & Theoretical Grounding

When explaining the system or presenting to evaluators, NetPulse Radar maps directly across the OSI model:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        OSI LAYER IMPLEMENTATION                        │
├─────────────────┬─────────────────────┬────────────────────────────────┤
│ OSI Layer       │ Networking Concept  │ NetPulse Radar Implementation  │
├─────────────────┼─────────────────────┼────────────────────────────────┤
│ Layer 7         │ Domain Name System  │ Upstream recursive resolver    │
│ (Application)   │ (DNS) & HTTP/SSE    │ benchmarking (1.1.1.1, etc.),  │
│                 │                     │ in-memory LRU cache (<0.05ms), │
│                 │                     │ Server-Sent Events stream.     │
├─────────────────┼─────────────────────┼────────────────────────────────┤
│ Layer 4         │ TCP / UDP Sockets   │ Real-time tracking of socket   │
│ (Transport)     │ & Bufferbloat       │ states (ESTABLISHED, LISTEN),  │
│                 │                     │ RTT handshake latency, jitter  │
│                 │                     │ variance, bufferbloat grading. │
├─────────────────┼─────────────────────┼────────────────────────────────┤
│ Layer 3         │ Path MTU Discovery  │ Transmits variable-length ICMP │
│ (Network)       │ (PMTUD) & IP Flags  │ echo requests with Don't       │
│                 │                     │ Fragment (DF) flags to detect  │
│                 │                     │ frame boundaries (1500 bytes). │
├─────────────────┼─────────────────────┼────────────────────────────────┤
│ Cross-Layer     │ Quality of Service  │ Applies Differentiated         │
│ (DiffServ)      │ (QoS) & DSCP        │ Services Code Points (DSCP 46  │
│                 │                     │ Expedited Forwarding, DSCP 34) │
│                 │                     │ via Windows NetQoS policies.   │
└─────────────────┴─────────────────────┴────────────────────────────────┘
```

---

## 5. System Architecture & End-to-End Data Pipeline

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         WINDOWS OPERATING SYSTEM                         │
│  [Physical NIC: Wi-Fi / Ethernet] ── [Active Sockets] ── [Process Table] │
└────────────────────┬─────────────────────────────────┬───────────────────┘
                     │                                 │
                     ▼                                 ▼
┌─────────────────────────────────────────┐ ┌──────────────────────────────┐
│         CORE: TELEMETRY ENGINE          │ │    CORE: NETWORK ANALYZER    │
│  • psutil.net_io_counters(pernic=True)  │ │  • TCP Handshake RTT Probing │
│  • psutil.net_connections(kind='inet')  │ │  • Jitter Variance Calculus  │
│  • Per-process Delta KB/s Tracking      │ │  • Bufferbloat Grading (A-F) │
│  • MAC Address PII Sanitization         │ │  • ICMP PMTUD Frame Probing  │
└────────────────────┬────────────────────┘ └──────────────┬───────────────┘
                     │                                     │
                     ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         CORE: SYSTEM CONTROLLERS                         │
│  • QoS Controller: Process Priority (psutil) + Windows NetQoS Policies   │
│  • DNS Optimizer: Upstream Benchmarking + Local LRU Memory Cache         │
│  • Report Generator: Certified Markdown & Print-Ready HTML Audits        │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         FLASK APPLICATION SERVER                         │
│  • In-Memory Sliding-Window Rate Limiter (DoS Defense)                   │
│  • RFC 1035 Regex Validator & IPv4 Address Sanitization                  │
│  • HTTP Security Headers Middleware (CSP, Frame-Options, nosniff)        │
│  • Server-Sent Events (SSE) Stream Endpoint (`/api/stream`)              │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       BROWSER CLIENT-SIDE INTERFACE                      │
│  • Chart.js 60fps Real-Time Throughput Curves                            │
│  • Process Telemetry Table & Protocol Distribution Bars                  │
│  • One-Click QoS Profile Switcher (Gaming / Work / Balanced / Throttle)  │
│  • Live DNS Benchmark & Sub-Millisecond Cache Test Bench                 │
│  • Spotlight Command Palette (`Ctrl + K`) & Certified Audit Reports      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Visual Tour of Features & Output Verification

Below are the actual high-resolution screenshots captured from the live, running NetPulse Radar instance, fully labeled and explained for inclusion in technical reports and presentations:

---

### Figure 1: Radar Overview Dashboard

![Figure 1: Radar Overview Dashboard](screenshots/01_radar_overview_dashboard.png)

* **Screenshot Path:** [`screenshots/01_radar_overview_dashboard.png`](screenshots/01_radar_overview_dashboard.png)
* **What This Output Shows:**
  1. **Top Status Bar:** Active physical network interface (`Wi-Fi [823 MBPS]`), execution mode (`USER SPACE`), and the real-time `LIVE RADAR` pulsing beacon.
  2. **Real-Time Key Performance Indicators (KPIs):**
     * **Inbound Traffic:** `18.71 KB/s` with an embedded SVG sparkline curve.
     * **Outbound Traffic:** `571.25 KB/s` with outbound egress sparkline.
     * **Edge Handshake RTT:** `8.1 ms` measured via direct socket ping.
     * **Bufferbloat Index:** Quality score grade with jitter and loss statistics.
  3. **Global Throughput Stream Chart:** Interactive Chart.js canvas rendering a rolling 30-second window distinguishing Inbound Download (Orange curve) and Outbound Upload (Cyan curve).
  4. **Traffic Distribution Analytics:** Application share breakdown (Web Browsers, Gaming & Voice, Collaboration, Bulk/OS Updates) alongside transport protocol segmentation (`TCP Stream 68%` vs `UDP Datagram 32%`).
  5. **Top Bandwidth-Consuming Processes:** Real-time table attributing network usage to specific executables (`ChatGPT.exe`, `language_server.exe`, `msedge.exe`) with PID, socket count, inbound/outbound throughput, and process priority.

---

### Figure 2: Quality of Service (QoS) Policy Engine

![Figure 2: Quality of Service (QoS) Policy Engine](screenshots/02_qos_traffic_controller.png)

* **Screenshot Path:** [`screenshots/02_qos_traffic_controller.png`](screenshots/02_qos_traffic_controller.png)
* **What This Output Shows:**
  1. **QoS Architecture:** Demonstrates the 4 policy profiles:
     * **Balanced (Default):** Standard OS scheduling with neutral DSCP 0.
     * **Gaming / Ultra-Low Latency:** DSCP 46 Expedited Forwarding on UDP gaming/voice ports.
     * **Work & Collaboration:** DSCP 34 Assured Forwarding prioritizing VoIP, Zoom, Teams, and WebRTC.
     * **Background Saver / Throttle:** DSCP 8 capping bulk P2P transfer threads.
  2. **Active Status Badge:** Shows the currently applied profile with real-time feedback.

---

### Figure 3: Active Gaming Profile & DSCP 46 Enforcement

![Figure 3: Active Gaming Profile](screenshots/03_qos_gaming_mode_active.png)

* **Screenshot Path:** [`screenshots/03_qos_gaming_mode_active.png`](screenshots/03_qos_gaming_mode_active.png)
* **What This Output Shows:**
  1. **Profile Activation:** The user selected **Gaming / Ultra-Low Latency**, highlighted by an active orange border and `HIGH PRIORITY` badge.
  2. **System Confirmation Toast:** The bottom-right notification confirms: `✓ QoS Profile "GAMING" active.`
  3. **Under-the-Hood Enforcement:** Discord and gaming processes were elevated to `psutil.HIGH_PRIORITY_CLASS`, background torrent/update processes were demoted to `psutil.IDLE_PRIORITY_CLASS`, and Windows NetQoS DSCP 46 policies were registered for active gaming ports.

---

### Figure 4: Upstream DNS Benchmark & Sub-Millisecond Cache

![Figure 4: Upstream DNS Benchmark & Sub-Millisecond Cache](screenshots/04_dns_benchmark_and_lru_cache.png)

* **Screenshot Path:** [`screenshots/04_dns_benchmark_and_lru_cache.png`](screenshots/04_dns_benchmark_and_lru_cache.png)
* **What This Output Shows:**
  1. **Multi-Resolver Benchmark:** Concurrently queried four major global recursive resolvers:
     * **Cloudflare (`1.1.1.1`):** `11.5 ms` — Ranked **FASTEST** (100% reliability).
     * **Google Public DNS (`8.8.8.8`):** `12.7 ms` (100% reliability).
     * **OpenDNS / Cisco (`208.67.222.222`):** `14.5 ms` (100% reliability).
     * **Quad9 (`9.9.9.9`):** `56.6 ms` (100% reliability).
  2. **Local In-Memory Caching Resolver:** Demonstrates the local LRU DNS cache query bench:
     * Resolved domain: `cloudflare.com` $\rightarrow$ `104.16.132.229, 104.16.133.229`.
     * **Cache Status:** `✓ CACHE HIT (<0.01ms)` with a verified latency of **`0.035 ms`** (over 99.7% faster than the recursive network lookup).
     * **Telemetry Counters:** Cache Entries: `1`, Hits: `1`, Misses: `1`, Hit Ratio: `50%`.

---

### Figure 5: Bufferbloat Jitter Analysis & Path MTU Discovery

![Figure 5: Bufferbloat Jitter Analysis & Path MTU Discovery](screenshots/05_bufferbloat_and_path_mtu.png)

* **Screenshot Path:** [`screenshots/05_bufferbloat_and_path_mtu.png`](screenshots/05_bufferbloat_and_path_mtu.png)
* **What This Output Shows:**
  1. **Bufferbloat Diagnostics:**
     * **Quality Grade:** `B`
     * **Verdict:** `GOOD`
     * **Average Jitter (Variance):** `11.9 ms` (calculated across rolling TCP handshake latency deltas).
     * **Packet Loss:** `0%`.
  2. **Path MTU Discovery (PMTUD):**
     * Probed target using ICMP Echo Requests with the Don't Fragment (DF) flag set across boundary payload sizes.
     * **Result:** `1500 bytes` — `No fragmentation detected`. Confirms the network interface operates at full standard Ethernet frame efficiency without MSS clamping penalties.

---

### Figure 6: Live Layer 4 Socket-to-Process Mapping

![Figure 6: Live Layer 4 Socket-to-Process Mapping](screenshots/06_live_socket_process_mapping.png)

* **Screenshot Path:** [`screenshots/06_live_socket_process_mapping.png`](screenshots/06_live_socket_process_mapping.png)
* **What This Output Shows:**
  1. **Direct Socket Inspection:** Maps active OS sockets directly to process binaries.
  2. **Granular Fields:**
     * **PID & Executable Name:** (e.g., `ChatGPT.exe`, `RazerCortex.exe`, `msedge.exe`, `nvcontainer.exe`, `ipfsvc.exe`).
     * **Protocol:** `TCP` (Stream).
     * **Local Socket Address:** Local IPv4/IPv6 and ephemeral source port.
     * **Remote Endpoint:** Target remote server IP and destination port (e.g., `:443` HTTPS).
     * **Socket State:** `ESTABLISHED` (active connection).

---

### Figure 7: Spotlight Command Palette (`Ctrl + K`)

![Figure 7: Spotlight Command Palette](screenshots/07_spotlight_command_palette.png)

* **Screenshot Path:** [`screenshots/07_spotlight_command_palette.png`](screenshots/07_spotlight_command_palette.png)
* **What This Output Shows:**
  1. **Keyboard-Driven Operations:** Pressing `Ctrl + K` launches a Spotlight search modal over the obsidian dashboard.
  2. **Instant Actions:** Allows rapid execution of commands:
     * *Enable Gaming / Low-Latency Mode (DSCP 46)*
     * *Enable Work & Video Conference Mode (DSCP 34)*
     * *Reset to Balanced Mode*
     * *Run Upstream DNS Benchmark*
     * *Export Executive Audit Report*

---

### Figure 8: Network Audit Report Generator Modal

![Figure 8: Network Audit Report Modal](screenshots/08_network_audit_report_modal.png)

* **Screenshot Path:** [`screenshots/08_network_audit_report_modal.png`](screenshots/08_network_audit_report_modal.png)
* **What This Output Shows:**
  1. **Audit Preview Engine:** Real-time compilation of all network diagnostic metrics into formatted Markdown.
  2. **Export Capabilities:** One-click actions to *Copy Markdown*, *Download `.md` file*, or launch the *Print / Save as PDF* clean layout.

---

### Figure 9: Print-Ready HTML Network Audit Report

![Figure 9: Print-Ready HTML Audit Report](screenshots/09_printable_html_audit_report.png)

* **Screenshot Path:** [`screenshots/09_printable_html_audit_report.png`](screenshots/09_printable_html_audit_report.png)
* **What This Output Shows:**
  1. **Executive Audit Layout:** Clean, publication-grade printable report formatted for institutional submission and client audits.
  2. **Complete Telemetry Snapshot:**
     * Link Health Grade, Active Interface (`Wi-Fi [823 Mbps]`), Active QoS Profile (`GAMING [DSCP 46]`), Handshake Latency & Jitter (`20.4 ms / 12.3 ms`).
     * Active process network consumption table.
     * Upstream DNS benchmark comparison table with reliability percentages and recommendations.
     * Local in-memory cache efficiency statistics.

---

## 7. Mathematical Formulations & Algorithmic Foundations

### 7.1 Real-Time Bandwidth Delta Calculus
To determine instantaneous inbound and outbound throughput without relying on external speed test traffic, NetPulse measures the differential byte count on the physical NIC over time:

$$\text{Throughput}_{\text{Inbound}} = \frac{\text{BytesRecv}(t_2) - \text{BytesRecv}(t_1)}{t_2 - t_1}$$

$$\text{Throughput}_{\text{Outbound}} = \frac{\text{BytesSent}(t_2) - \text{BytesSent}(t_1)}{t_2 - t_1}$$

Converting to human-readable units:
$$\text{Rate (KB/s)} = \frac{\text{Bytes/sec}}{1024}, \quad \text{Rate (Mbps)} = \frac{\text{Bytes/sec} \times 8}{1024 \times 1024}$$

### 7.2 RTT Jitter Variance Calculation
Jitter represents the statistical instability of network latency. NetPulse maintains a rolling FIFO queue of the last $N = 20$ round-trip time measurements ($RTT_1, RTT_2, \dots, RTT_N$) obtained through non-blocking TCP handshakes:

$$\text{Jitter} = \frac{1}{N-1} \sum_{i=1}^{N-1} |RTT_{i+1} - RTT_i|$$

A connection with a constant 25ms RTT produces $\text{Jitter} \approx 0\text{ ms}$, indicating an optimal queue. If RTT fluctuates widely (e.g., alternating between 15ms and 85ms), $\text{Jitter} > 30\text{ ms}$, signaling router buffer congestion.

### 7.3 Bufferbloat Health Grading Algorithm
NetPulse evaluates connection quality based on latency inflation, jitter variance, and packet loss:

$$\text{Grade} = 
\begin{cases}
\mathbf{F} & \text{if } \text{Loss} > 5\% \text{ or } RTT > 250\text{ ms} \\
\mathbf{D} & \text{if } RTT > 120\text{ ms} \text{ or } \text{Jitter} > 30\text{ ms} \\
\mathbf{C} & \text{if } RTT > 65\text{ ms} \text{ or } \text{Jitter} > 15\text{ ms} \\
\mathbf{B} & \text{if } RTT > 35\text{ ms} \text{ or } \text{Jitter} > 8\text{ ms} \\
\mathbf{A} & \text{if } RTT > 20\text{ ms} \text{ or } \text{Jitter} > 4\text{ ms} \\
\mathbf{A+} & \text{otherwise (Optimal Latency)}
\end{cases}$$

### 7.4 In-Memory LRU Cache Hit Ratio
$$\text{Cache Hit Ratio (\%)} = \left(\frac{\text{Hits}}{\text{Hits} + \text{Misses}}\right) \times 100$$

When a domain record is queried:
* **Cache Miss:** Queries external resolver via UDP port 53. Latency: $15\text{ ms} - 60\text{ ms}$. Record saved with $\text{ExpiresAt} = t_{\text{now}} + \min(\text{TTL}, 300)$.
* **Cache Hit:** Read directly from memory hash table. Latency: $<0.05\text{ ms}$ (a $>99\%$ latency reduction).

---

## 8. Defensive Security Architecture & Threat Defenses

To ensure NetPulse Radar is safe for enterprise deployment and immune to common web and network vulnerabilities, the codebase implements strict defensive controls:

1. **Command Injection Prevention:** All system commands executed via `subprocess` completely avoid the shell (`shell=False`) and pass arguments as discrete, parameterized token arrays:
   ```python
   # SAFE: Shell metacharacters are treated as literal arguments
   subprocess.run(["ping", "-f", "-l", str(payload), safe_target, "-n", "1"], shell=False)
   ```
2. **Strict RFC 1035 Domain Validation:** All domain inputs must conform to RFC 1035 regex specifications ($\le 253$ characters, valid label formatting):
   ```python
   pattern = r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-_]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-_]{1,63}(?<!-))*\.?$'
   ```
3. **Sliding-Window Rate Limiting:** An in-memory rate limiter tracks request timestamps per client IP over a 60-second rolling window. Heavy endpoints (DNS benchmark, MTU scan, QoS policy changes) are strictly capped to 10 requests per minute to prevent resource exhaustion and DoS attacks.
4. **HTTP Security Headers & CSP:** Every response includes:
   * `Content-Security-Policy`: Scripts restricted to `'self'` and trusted CDNs; `frame-ancestors 'none'`.
   * `X-Frame-Options: DENY`: Blocks iframe embedding and Clickjacking.
   * `X-Content-Type-Options: nosniff`: Prevents MIME-confusion attacks.
   * `Referrer-Policy: strict-origin-when-cross-origin`: Blocks referrer leakage.
5. **Origin & CSRF Defense:** Enforces matching `Origin` and `Referer` headers on all state-changing `POST` endpoints.
6. **Localhost Binding:** Binds strictly to `127.0.0.1` by default, ensuring external devices on the local network cannot access or alter local QoS policies.
7. **PII Sanitization:** Hardware MAC addresses are sanitized (`**:**:**:**:XX:XX`) before being emitted in telemetry streams or reports to prevent hardware fingerprinting.

---

## 9. 3-Member Presentation Guide & Turn-by-Turn Speaking Scripts

Divide your presentation cleanly among your 3 team members so that each person covers a distinct, high-impact area:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        3-MEMBER DIVISION PLAN                          │
├────────────────────┬────────────────────┬──────────────────────────────┤
│ Member 1           │ Member 2           │ Member 3                     │
│ Project Vision,    │ Traffic Engine,    │ DNS Engine, Local Cache      │
│ Real-Time Streams  │ Dual-Tier QoS &    │ & Defensive Security         │
│ & Telemetry UI     │ Bufferbloat/PMTUD  │ Hardening                    │
└────────────────────┴────────────────────┴──────────────────────────────┘
```

---

### Member 1: System Vision, Telemetry Engine & Live Dashboard

* **Core Focus:** Why the project was built, physical NIC delta calculation, process-to-socket attribution, Server-Sent Events (SSE), and the Cloudflare Radar UI.
* **Speaking Script:**
  > *"Good morning/afternoon. Today our team is presenting **NetPulse Radar**, an endpoint network controller and traffic optimization platform built for Windows.*  
  > 
  > *In conventional networking courses, students are typically introduced to simulators like Cisco Packet Tracer or Mininet. While these tools teach fundamental routing concepts, they simulate synthetic packets in a closed sandbox. They cannot show you how real operating system sockets behave or how background processes saturate a physical Wi-Fi interface.*  
  > 
  > *NetPulse Radar interfaces directly with the live Windows network stack. My focus was the **Telemetry Engine and the Real-Time Streaming Architecture**.*  
  > 
  > *Every 1000 milliseconds, NetPulse samples the physical network interface's I/O counters via `psutil`. By calculating the byte delta over elapsed time, we compute precise inbound and outbound bandwidth rates in both KB/s and Mbps.*  
  > 
  > *Furthermore, NetPulse inspects the OS socket table. As shown in **Figure 1**, every active connection is mapped directly to its owning Process ID (PID). For example, if a background process is hogging bandwidth, NetPulse immediately surfaces its executable name, category, and socket count.*  
  > 
  > *To stream this telemetry to the client without latency, we implemented **Server-Sent Events (SSE)** via HTTP. Unlike WebSockets which require bidirectional protocol upgrades and heavy framing, SSE is lightweight, unidirectional, and natively handles reconnection in the browser. Our UI uses Chart.js to render rolling 60fps throughput curves with a Cloudflare Radar obsidian aesthetic.*  
  > 
  > *I will now hand over to [Member 2], who will explain our Quality of Service controller and bufferbloat diagnostics."*

* **Screenshots to Show:**
  * [Figure 1: Radar Overview Dashboard](screenshots/01_radar_overview_dashboard.png)
  * [Figure 7: Spotlight Command Palette](screenshots/07_spotlight_command_palette.png)

---

### Member 2: Quality of Service (QoS), Bufferbloat & Path MTU Discovery

* **Core Focus:** Dual-Tier QoS enforcement, DSCP packet tagging (DiffServ), Bufferbloat theory, RTT Jitter calculus, and ICMP Path MTU Discovery.
* **Speaking Script:**
  > *"Thank you [Member 1]. While monitoring traffic is valuable, true network engineering requires the ability to **actively shape and prioritize** that traffic. That brings us to our **QoS Controller and Bufferbloat Diagnostics**.*  
  > 
  > *Network congestion often occurs when bulk downloads saturate the router's queue, introducing packet delay for latency-sensitive applications like gaming and video conferencing. NetPulse implements **Dual-Tier QoS**:*  
  > 
  > *First, at the **User-Space level**, NetPulse adjusts Windows process scheduling priorities. As shown in **Figures 2 and 3**, when Gaming Mode is activated, background torrent and update processes are throttled to `IDLE_PRIORITY`, while game binaries and Discord are boosted to `HIGH_PRIORITY`.*  
  > 
  > *Second, at the **Kernel level**, NetPulse uses Windows NetQoS policies via PowerShell to apply **DSCP (Differentiated Services Code Point)** tags directly onto IP packet headers. We tag real-time gaming packets with **DSCP 46 (Expedited Forwarding)** and video conferencing packets with **DSCP 34 (Assured Forwarding)**. Upstream routers inspect these tags and prioritize these packets ahead of best-effort traffic.*  
  > 
  > *Next, we address **Bufferbloat**. As shown in **Figure 5**, NetPulse measures connection RTT via raw TCP handshakes and computes **Jitter** as the mean absolute difference between consecutive samples. Based on jitter and packet loss, our algorithm issues an objective connection grade from A+ down to F.*  
  > 
  > *Finally, our **Path MTU Discovery (PMTUD)** module sends ICMP echo packets with the Don't Fragment (DF) flag set across boundary payload sizes, confirming that our link handles standard 1500-byte frames without fragmentation overhead.*  
  > 
  > *I will now pass the floor to [Member 3], who will explain our DNS caching engine and defensive security architecture."*

* **Screenshots to Show:**
  * [Figure 2: Quality of Service Policy Engine](screenshots/02_qos_traffic_controller.png)
  * [Figure 3: Active Gaming Profile & DSCP 46](screenshots/03_qos_gaming_mode_active.png)
  * [Figure 5: Bufferbloat Jitter Analysis & Path MTU](screenshots/05_bufferbloat_and_path_mtu.png)

---

### Member 3: Upstream DNS Benchmarking, Local Cache & Security Hardening

* **Core Focus:** DNS resolution lifecycle, recursive resolver benchmarking, in-memory LRU caching (<0.05ms response), defensive security (rate limiting, CSP, command injection prevention), and audit reporting.
* **Speaking Script:**
  > *"Thank you [Member 2]. I will be covering our **DNS Optimization Engine and Defensive Security Architecture**.*  
  > 
  > *Every web session begins with a DNS lookup. Default ISP resolvers are frequently slow, congested, or unencrypted.*  
  > 
  > *NetPulse incorporates an **Upstream DNS Benchmarking Engine** powered by `dnspython`. As shown in **Figure 4**, it concurrently queries four leading public resolvers—Cloudflare `1.1.1.1`, Google `8.8.8.8`, OpenDNS, and Quad9—measuring recursive lookup latencies and highlighting the fastest provider.*  
  > 
  > *To eliminate internet lookup latency entirely for repeated queries, NetPulse includes a **Local Thread-Safe In-Memory DNS Cache**. On the initial query, the domain is resolved over the internet, taking 15 to 40 milliseconds. NetPulse stores the resolved IP addresses in an LRU hash table along with their TTL. On subsequent queries, the answer is served directly from RAM in **0.035 milliseconds**—a 99.7% speed improvement!*  
  > 
  > *Security was engineered into NetPulse from the foundation:*  
  > *1. **Command Injection Immunity:** Subprocess calls strictly avoid `shell=True` and pass discrete argument lists, neutralizing shell metacharacter injection.*  
  > *2. **RFC 1035 Validation:** Domain queries are sanitized via strict regex rules, and IP inputs are parsed with Python’s `ipaddress` library.*  
  > *3. **Sliding-Window Rate Limiting:** Diagnostic endpoints are capped to 10 requests per minute to prevent resource starvation.*  
  > *4. **Security Headers:** Enforces Content Security Policy, blocks clickjacking with `X-Frame-Options: DENY`, prevents MIME sniffing, and masks hardware MAC addresses.*  
  > 
  > *Finally, as shown in **Figures 8 and 9**, NetPulse can compile all diagnostics into certified **Network Audit Reports** in both Markdown and print-ready HTML formats.*  
  > 
  > *This concludes our presentation, and we welcome your questions."*

* **Screenshots to Show:**
  * [Figure 4: Upstream DNS Benchmark & Cache](screenshots/04_dns_benchmark_and_lru_cache.png)
  * [Figure 6: Live Socket-to-Process Mapping](screenshots/06_live_socket_process_mapping.png)
  * [Figure 8: Network Audit Report Modal](screenshots/08_network_audit_report_modal.png)
  * [Figure 9: Print-Ready HTML Audit Report](screenshots/09_printable_html_audit_report.png)

---

## 10. Viva & Technical Examination Defense Bank (15 Questions)

Use this question bank to prepare for evaluation panels and technical viva examinations:

---

### Q1: "Is NetPulse Radar merely a wrapper around Wireshark or `tshark`?"
**Answer:**  
> *"No. Wireshark requires packet capture kernel drivers (like Npcap or WinPcap) to operate in promiscuous packet capture mode at Layer 2. NetPulse Radar is an **endpoint telemetry and control system**. It interfaces directly with the Windows OS subsystem using `psutil` to inspect kernel socket tables, physical NIC I/O counters, and process scheduling queues. Furthermore, Wireshark is purely passive—it only observes traffic. NetPulse is active: it adjusts thread priorities, writes Windows NetQoS DSCP policies, and operates an in-memory caching DNS resolver."*

---

### Q2: "Why choose Server-Sent Events (SSE) over WebSockets for the live dashboard?"
**Answer:**  
> *"WebSockets are designed for bidirectional full-duplex communication, which is necessary when both client and server transmit messages frequently (like collaborative whiteboards or online games). However, our telemetry stream is strictly **unidirectional**—the server broadcasts metrics to the browser every 1000ms. Server-Sent Events run over standard HTTP, require zero connection upgrade handshakes, support automatic client-side reconnection out of the box via JavaScript's `EventSource`, have lower memory overhead, and pass cleanly through standard firewalls and reverse proxies."*

---

### Q3: "What is DSCP and how does Windows enforce it?"
**Answer:**  
> *"DSCP stands for **Differentiated Services Code Point** (RFC 2474). It is a 6-bit field in the IPv4 Type of Service (ToS) header (or IPv6 Traffic Class header) that network routers inspect to classify traffic into priority queues. When NetPulse activates Gaming Mode, it executes PowerShell's `New-NetQosPolicy` to register a kernel policy matching UDP gaming ports and assigning **DSCP 46 (Expedited Forwarding)**. When packets leave the network adapter, the Windows TCP/IP stack writes `0x2E` into the IP header, signaling switches and routers to prioritize these packets over best-effort traffic."*

---

### Q4: "How does the local DNS cache achieve latency below 0.05ms?"
**Answer:**  
> *"Standard DNS resolution requires transmitting a UDP datagram over the physical network to an external recursive resolver (such as `1.1.1.1`), which involves physical propagation delay, router queuing, and recursive upstream queries, taking 15 to 60 milliseconds. NetPulse’s `DnsCache` maintains an in-memory Python hash table mapping domain names to IP lists and expiry timestamps. When a query hits the cache, it is retrieved via an $O(1)$ memory lookup, completely bypassing the network adapter and OS socket stack, resolving in under 0.05 milliseconds."*

---

### Q5: "What is Bufferbloat and why does high bandwidth not prevent it?"
**Answer:**  
> *"Bufferbloat is severe latency inflation caused by excessive, unmanaged packet buffering in network routers and modems under load. Even on a 500 Mbps connection, if an application initiates a large download, the router's queue fills with bulk packets. Real-time packets (such as VoIP audio frames or gaming UDP ticks) get queued behind these bulk buffers, causing latency to spike from 15ms to over 300ms. NetPulse measures bufferbloat by monitoring RTT jitter variance during active traffic and assigns an objective health grade from A+ to F."*

---

### Q6: "How does Path MTU Discovery (PMTUD) operate in your code?"
**Answer:**  
> *"The Maximum Transmission Unit (MTU) is the largest IP packet size that can transit a link without fragmentation (standard Ethernet is 1500 bytes). NetPulse’s `test_mtu()` function sends ICMP echo requests with the **Don't Fragment (DF)** flag enabled across boundary payload sizes (1472 bytes + 28 bytes of IP/ICMP headers = 1500 bytes). If an intermediate router has an MTU lower than 1500, it drops the packet and responds with an ICMP 'Fragmentation Needed' message. If the 1500-byte frame passes with 0% loss, NetPulse confirms optimal frame transmission without fragmentation overhead."*

---

### Q7: "What happens if NetPulse is run without Administrator privileges?"
**Answer:**  
> *"NetPulse implements **graceful degradation**:*  
> * *In **Standard User Mode**, the Telemetry Engine, live socket mapping, DNS benchmarking, local caching resolver, Bufferbloat diagnostics, and user-space process priority adjustments (`psutil.HIGH_PRIORITY_CLASS` / `IDLE_PRIORITY_CLASS`) function completely.*  
> * *When elevated to **Administrator** via `run_admin.bat`, NetPulse unlocks kernel-space Windows NetQoS policies, enabling hardware-level DSCP packet tagging and system-wide adapter DNS reconfiguration.*  
> *The UI displays an active badge (`User Space` vs `Admin Mode`) reflecting the current privilege level."*

---

### Q8: "How does your code prevent Command Injection vulnerabilities?"
**Answer:**  
> *"In Python, command injection occurs when untrusted input is passed to `subprocess` or `os.system` with `shell=True`, allowing attackers to concatenate malicious operators like `;`, `&`, or `|`. In NetPulse, every subprocess call sets `shell=False` and passes command arguments as discrete, parameterized elements in a list (e.g., `['ping', '-f', '-l', str(payload), safe_target]`). Because no command shell is invoked, metacharacters are treated as literal text and cannot execute arbitrary commands."*

---

### Q9: "How does your rate limiter protect against Denial of Service (DoS)?"
**Answer:**  
> *"In `web/server.py`, we implemented a thread-safe sliding-window `RateLimiter` class. It maintains a timestamp log per client IP for a rolling 60-second window. Heavy diagnostic endpoints (such as `/api/dns/benchmark` and `/api/analyzer/mtu`) are capped at 10 requests per minute. If a client exceeds this quota, the server immediately returns HTTP status code `429 Too Many Requests` with a `Retry-After` header. This prevents abusive requests from exhausting system CPU or flooding external DNS servers."*

---

### Q10: "Why does NetPulse bind to `127.0.0.1` by default rather than `0.0.0.0`?"
**Answer:**  
> *"Binding to `0.0.0.0` exposes the server to all network interfaces on the host, including untrusted public Wi-Fi networks. Because NetPulse controls OS process priority scheduling and network policies, exposing the dashboard on `0.0.0.0` without enterprise authentication would allow any device on the same local network to alter network configurations. Binding strictly to `127.0.0.1` (localhost) guarantees that only local processes can access the API."*

---

### Q11: "What is the difference between TCP and UDP sockets in your telemetry view?"
**Answer:**  
> *"TCP is a connection-oriented, reliable transport protocol that uses a three-way handshake, sequence numbers, and acknowledgments to ensure ordered delivery; sockets in our table reflect explicit states such as `ESTABLISHED` or `LISTEN`. UDP is a connectionless, best-effort protocol that operates without handshakes or retransmissions, making it ideal for real-time voice and gaming. NetPulse identifies TCP connections with their full connection state and displays active UDP endpoints."*

---

### Q12: "How is Jitter calculated in your analyzer engine?"
**Answer:**  
> *"Jitter measures the statistical variance in packet arrival latency. In `core/analyzer.py`, we maintain a rolling FIFO buffer of the last 20 round-trip time (RTT) measurements taken via non-blocking TCP socket handshakes. We calculate Jitter as the mean of the absolute differences between consecutive RTT samples:*  
> $$\text{Jitter} = \frac{\sum_{i=1}^{N-1} |RTT_{i+1} - RTT_i|}{N-1}$$  
> *A stable connection with steady 15ms latency yields $\text{Jitter} < 2\text{ ms}$, whereas an unstable connection fluctuating between 15ms and 80ms yields high jitter, indicating queuing delay."*

---

### Q13: "What prevents the in-memory DNS cache from overflowing memory?"
**Answer:**  
> *"Our `DnsCache` class enforces two bounding mechanisms: First, it enforces a strict capacity ceiling of 1,000 domain records. When full, it purges expired records whose TTL has elapsed; if all records remain active, it evicts the oldest record using a First-In, First-Out (FIFO) policy. Second, each cached record has an expiration timestamp based on the upstream TTL with a maximum ceiling of 300 seconds, preventing stale IP resolution."*

---

### Q14: "What security headers are enforced and what attacks do they prevent?"
**Answer:**  
> *"In `web/server.py`, our `add_security_headers` middleware injects four critical headers on every response:*  
> *1. `Content-Security-Policy (CSP)`: Restricts script and style execution strictly to self-hosted files and whitelisted CDNs, blocking Cross-Site Scripting (XSS).*  
> *2. `X-Frame-Options: DENY` and `frame-ancestors 'none'`: Prevents the dashboard from being embedded inside an `<iframe>`, neutralizing Clickjacking attacks.*  
> *3. `X-Content-Type-Options: nosniff`: Prevents browsers from overriding the declared MIME type, mitigating MIME-confusion attacks.*  
> *4. `Referrer-Policy: strict-origin-when-cross-origin`: Prevents sensitive internal URL parameters from leaking to external referrers."*

---

### Q15: "What makes NetPulse Radar a compelling Computer Networks capstone project?"
**Answer:**  
> *"NetPulse Radar directly demonstrates the core theoretical pillars of Computer Networks in a running, tangible system:*  
> *1. **Application Layer (Layer 7):** Recursive DNS resolution, authoritative caching, TTL handling, and HTTP/SSE streaming.*  
> *2. **Transport Layer (Layer 4):** TCP connection state tracking, socket-to-process attribution, RTT measurement, and jitter variance analysis.*  
> *3. **Network Layer (Layer 3):** IP packet routing, Path MTU Discovery, ICMP fragmentation flags, and IPv4 address validation.*  
> *4. **Cross-Layer Traffic Engineering:** Differentiated Services (DiffServ) DSCP tagging, queue prioritization, and bufferbloat mitigation.*  
> *Instead of viewing diagrams in a textbook, NetPulse makes these protocols observable, measurable, and controllable on a live operating system."*
