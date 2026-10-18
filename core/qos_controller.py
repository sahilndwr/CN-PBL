import os
import ctypes
import subprocess
import psutil
from typing import Dict, List, Any, Optional

QOS_PROFILES = {
    "balanced": {
        "id": "balanced",
        "name": "Balanced (Default)",
        "badge": "Standard",
        "description": "Default operating system scheduling with neutral DSCP tagging.",
        "icon": "activity",
        "dscp": 0
    },
    "gaming": {
        "id": "gaming",
        "name": "Gaming / Ultra-Low Latency",
        "badge": "High Priority",
        "description": "Applies DSCP 46 (Expedited Forwarding) on UDP gaming/voice ports. Throttles background download threads.",
        "icon": "zap",
        "dscp": 46
    },
    "work": {
        "id": "work",
        "name": "Work & Collaboration",
        "badge": "Interactive",
        "description": "Prioritizes VoIP and video streaming (Zoom, Teams, WebRTC) with DSCP 34 (Assured Forwarding).",
        "icon": "video",
        "dscp": 34
    },
    "download_throttle": {
        "id": "download_throttle",
        "name": "Background Saver / Throttle",
        "badge": "Eco Mode",
        "description": "Caps aggressive bulk downloaders to protect ping and web browsing responsiveness.",
        "icon": "shield",
        "dscp": 8
    }
}

class QosController:
    def __init__(self):
        self.active_profile = "balanced"
        self.is_elevated = self._check_elevation()
        self.applied_policies: List[str] = []

    def _check_elevation(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "active_profile": self.active_profile,
            "profile_details": QOS_PROFILES.get(self.active_profile, QOS_PROFILES["balanced"]),
            "is_elevated": self.is_elevated,
            "all_profiles": list(QOS_PROFILES.values()),
            "applied_policies": self.applied_policies
        }

    def apply_profile(self, profile_id: str) -> Dict[str, Any]:
        if profile_id not in QOS_PROFILES:
            return {"success": False, "error": f"Unknown profile: {profile_id}"}

        self.active_profile = profile_id
        user_space_applied = self._apply_user_space_priorities(profile_id)
        os_applied = False
        os_msg = ""

        if self.is_elevated:
            os_applied, os_msg = self._apply_windows_netqos(profile_id)
        else:
            os_msg = "Running in Standard User mode. Process-level prioritization applied. (Run as Admin for kernel NetQoS policies)."

        return {
            "success": True,
            "profile": profile_id,
            "user_space_applied": user_space_applied,
            "os_netqos_applied": os_applied,
            "message": os_msg
        }

    def _apply_user_space_priorities(self, profile_id: str) -> int:
        count = 0
        try:
            for p in psutil.process_iter(['name']):
                try:
                    name = p.name().lower()
                    if profile_id == "gaming":
                        if any(k in name for k in ["discord", "steam", "valorant", "csgo", "dota", "epicgames"]):
                            p.nice(psutil.HIGH_PRIORITY_CLASS)
                            count += 1
                        elif any(k in name for k in ["torrent", "qbittorrent", "idm"]):
                            p.nice(psutil.IDLE_PRIORITY_CLASS)
                            count += 1
                    elif profile_id == "work":
                        if any(k in name for k in ["zoom", "teams", "slack", "webex", "chrome", "msedge"]):
                            p.nice(psutil.HIGH_PRIORITY_CLASS)
                            count += 1
                        elif any(k in name for k in ["torrent", "steam"]):
                            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                            count += 1
                    elif profile_id == "download_throttle":
                        if any(k in name for k in ["torrent", "qbittorrent", "steam", "epicgames"]):
                            p.nice(psutil.IDLE_PRIORITY_CLASS)
                            count += 1
                    elif profile_id == "balanced":
                        if any(k in name for k in ["discord", "steam", "zoom", "teams", "torrent", "qbittorrent"]):
                            p.nice(psutil.NORMAL_PRIORITY_CLASS)
                            count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return count

    def _apply_windows_netqos(self, profile_id: str) -> tuple[bool, str]:
        self._clear_netqos()

        if profile_id == "balanced":
            return True, "NetQoS policies reset to default balanced."

        commands = []
        if profile_id == "gaming":
            commands.append("New-NetQosPolicy -Name 'NetPulse_Gaming_Voice' -IPProtocol UDP -LocalPort 5000-5500 -DSCPAction 46 -PolicyStore ActiveStore")
            commands.append("New-NetQosPolicy -Name 'NetPulse_Gaming_Direct' -IPProtocol UDP -LocalPort 27000-27050 -DSCPAction 46 -PolicyStore ActiveStore")
            self.applied_policies = ["NetPulse_Gaming_Voice", "NetPulse_Gaming_Direct"]
        elif profile_id == "work":
            commands.append("New-NetQosPolicy -Name 'NetPulse_VoIP' -IPProtocol UDP -LocalPort 5060 -DSCPAction 46 -PolicyStore ActiveStore")
            commands.append("New-NetQosPolicy -Name 'NetPulse_WebRTC' -IPProtocol UDP -LocalPort 3478 -DSCPAction 34 -PolicyStore ActiveStore")
            self.applied_policies = ["NetPulse_VoIP", "NetPulse_WebRTC"]
        elif profile_id == "download_throttle":
            commands.append("New-NetQosPolicy -Name 'NetPulse_Bulk_P2P' -AppPathNameMatchCondition 'qbittorrent.exe' -ThrottleRateActionBitsPerSecond 1000000 -PolicyStore ActiveStore")
            self.applied_policies = ["NetPulse_Bulk_P2P"]

        output_msgs = []
        for cmd in commands:
            try:
                proc = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=5)
                if proc.returncode == 0:
                    output_msgs.append("Applied successfully")
                else:
                    output_msgs.append(proc.stderr.strip())
            except Exception as e:
                output_msgs.append(str(e))

        return True, f"Windows NetQoS Policies active ({len(self.applied_policies)} registered)."

    def _clear_netqos(self):
        ps = "Get-NetQosPolicy -PolicyStore ActiveStore | Where-Object { $_.Name -like 'NetPulse_*' } | Remove-NetQosPolicy -Confirm:$false"
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=5)
            self.applied_policies = []
        except Exception:
            pass
