"""
SIGMA_ASR_VTT — Deep Multi-Component Hardware Fingerprint Generator (V3).
Developer: أصيل السويدي

Aggregates 8 distinct hardware components on Windows into a single cryptographically
secure and stable hardware fingerprint:
1. Motherboard Serial Number (Win32_BaseBoard)
2. Computer System Product UUID (Win32_ComputerSystemProduct)
3. BIOS Serial Number (Win32_BIOS)
4. CPU Processor ID (Win32_Processor)
5. Primary Disk Drive Serial Number (Win32_DiskDrive)
6. Windows MachineGuid (Registry: HKLM\\SOFTWARE\\Microsoft\\Cryptography)
7. Physical Network Adapter MAC Address (Win32_NetworkAdapterConfiguration)
8. GPU Video Controller PNP Device ID (Win32_VideoController)

Format: SIGMA-XXXX-XXXX-XXXX-XXXX
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess  # nosec B404
from typing import Dict, Optional

_CREATE_NO_WINDOW = 0x08000000


def _get_machine_guid_winreg() -> str:
    """Read Windows MachineGuid from registry (stable across reboots)."""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
        )
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return str(value).strip().upper()
    except Exception:
        return ""


def _query_all_hardware_cim() -> Dict[str, str]:
    """
    Executes a single consolidated PowerShell batch query to extract all CIM metrics in one pass.
    """
    ps_script = """
$ErrorActionPreference = 'SilentlyContinue'
$board = (Get-CimInstance Win32_BaseBoard).SerialNumber
$uuid = (Get-CimInstance Win32_ComputerSystemProduct).UUID
$bios = (Get-CimInstance Win32_BIOS).SerialNumber
$cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1).ProcessorId
$disk = (Get-CimInstance Win32_DiskDrive | Select-Object -First 1).SerialNumber
$mac = (Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled -eq $true } | Select-Object -First 1).MACAddress
$gpu = (Get-CimInstance Win32_VideoController | Select-Object -First 1).PNPDeviceID

@{
    baseboard_serial = $board
    system_uuid = $uuid
    bios_serial = $bios
    cpu_id = $cpu
    disk_serial = $disk
    mac_address = $mac
    gpu_pnp = $gpu
} | ConvertTo-Json -Compress
"""
    try:
        ps_path = shutil.which("powershell") or "powershell"
        full_cmd = [ps_path, "-NoProfile", "-NonInteractive", "-Command", ps_script]
        result = subprocess.check_output(  # nosec B603
            full_cmd,
            stderr=subprocess.DEVNULL,
            creationflags=_CREATE_NO_WINDOW,
            timeout=8,
        ).decode("utf-8", errors="ignore").strip()

        if result:
            raw_dict = json.loads(result)
            cleaned = {}
            for k, v in raw_dict.items():
                val_str = str(v).strip().upper() if v else ""
                if val_str and val_str.lower() not in ("none", "to be filled by o.e.m.", "default string"):
                    cleaned[k] = val_str
                else:
                    cleaned[k] = ""
            return cleaned
    except Exception:
        pass

    return {
        "baseboard_serial": "",
        "system_uuid": "",
        "bios_serial": "",
        "cpu_id": "",
        "disk_serial": "",
        "mac_address": "",
        "gpu_pnp": ""
    }


class HWIDGenerator:
    """
    Deterministic machine fingerprint generator with deep hardware inspection.
    Combines 8 hardware identifiers into a single SHA-256 hash.
    The result is formatted as SIGMA-XXXX-XXXX-XXXX-XXXX.
    """

    _cached_hwid: Optional[str] = None
    _cached_details: Optional[Dict[str, str]] = None
    _SALT = "SIGMA_VTT_ENTERPRISE_HWID_SECURITY_SALT_2026_YEMEN"

    @classmethod
    def get_hardware_details(cls, force_refresh: bool = False) -> Dict[str, str]:
        """Returns the dictionary of all 8 extracted hardware metrics."""
        if cls._cached_details is not None and not force_refresh:
            return cls._cached_details

        if sys.platform == "win32":
            cim_data = _query_all_hardware_cim()
            guid = _get_machine_guid_winreg()
            cim_data["machine_guid"] = guid
        else:
            # Fallback for mock/test environments
            import platform
            import uuid
            cim_data = {
                "baseboard_serial": platform.node(),
                "system_uuid": str(uuid.getnode()),
                "bios_serial": platform.processor() or "VIRTUAL_BIOS",
                "cpu_id": platform.machine(),
                "disk_serial": "TEST_BOOT_DISK_001",
                "machine_guid": "LINUX-OR-TEST-MACHINE-GUID",
                "mac_address": ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1]).upper(),
                "gpu_pnp": "VIRTUAL_GPU_ADAPTER"
            }

        cls._cached_details = cim_data
        return cim_data

    @classmethod
    def generate(cls, force_refresh: bool = False) -> str:
        """Generates canonical Hardware ID string (SIGMA-XXXX-XXXX-XXXX-XXXX)."""
        if cls._cached_hwid is not None and not force_refresh:
            return cls._cached_hwid

        details = cls.get_hardware_details(force_refresh=force_refresh)

        components = [
            details.get("baseboard_serial", ""),
            details.get("system_uuid", ""),
            details.get("bios_serial", ""),
            details.get("cpu_id", ""),
            details.get("disk_serial", ""),
            details.get("machine_guid", ""),
            details.get("mac_address", ""),
            details.get("gpu_pnp", "")
        ]

        raw_data = "|".join(c for c in components if c)

        if not raw_data:
            # Registry Windows ProductId Fallback
            try:
                import winreg

                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
                )
                product_id, _ = winreg.QueryValueEx(key, "ProductId")
                winreg.CloseKey(key)
                raw_data = f"FALLBACK|{product_id}|{os.environ.get('COMPUTERNAME', '')}"
            except Exception:
                raw_data = f"FALLBACK|{os.environ.get('COMPUTERNAME', 'SIGMA')}|{os.environ.get('USERNAME', 'USER')}"

        salted_data = f"{cls._SALT}|{raw_data}"
        full_hash = hashlib.sha256(salted_data.encode("utf-8")).hexdigest().upper()
        hwid = f"SIGMA-{full_hash[0:4]}-{full_hash[4:8]}-{full_hash[8:12]}-{full_hash[12:16]}"
        cls._cached_hwid = hwid
        return hwid
