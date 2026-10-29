#!/usr/bin/env python
"""
SIGMA_ASR_VTT - Developer Master Key Generator (KeyGen)
Developer: أصيل السويدي

Generates cryptographically signed, hardware-bound Ed25519 licenses.
Supports Lifetime, Custom Hours, Custom Days, and Custom Expiry Dates.
Format: SIGMA-LIC-<payload_b64>.<signature_b64>
"""

import os
import sys
import json
import base64
import time
import secrets
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

PRIVATE_KEY_PATH = BASE_DIR / "keys" / "license_private_key.pem"


def load_or_create_private_key() -> ed25519.Ed25519PrivateKey:
    """Loads developer private key or creates a new one if missing."""
    if PRIVATE_KEY_PATH.exists():
        pem_data = PRIVATE_KEY_PATH.read_bytes()
        return serialization.load_pem_private_key(pem_data, password=None)
    
    PRIVATE_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    priv_key = ed25519.Ed25519PrivateKey.generate()
    pem_bytes = priv_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    PRIVATE_KEY_PATH.write_bytes(pem_bytes)
    print(f"[!] New Developer Private Key generated at: {PRIVATE_KEY_PATH}")
    return priv_key


def generate_license_token(
    hwid: str,
    client_name: str,
    license_type: str = "lifetime",
    duration_hours: float = None,
    duration_days: float = None,
    custom_expiry_timestamp: int = None,
    plan: str = "PRO"
) -> tuple:
    """
    Signs and packs an Ed25519 license token matching LicenseValidator V2.
    """
    priv_key = load_or_create_private_key()
    now_ts = int(datetime.now(timezone.utc).timestamp())
    
    expires_at = 0  # 0 indicates Lifetime
    is_time_limited = (
        license_type in ("time_limited", "hours", "days")
        or duration_hours is not None
        or duration_days is not None
        or custom_expiry_timestamp is not None
    ) and license_type != "lifetime"

    if is_time_limited:
        if custom_expiry_timestamp:
            expires_at = int(custom_expiry_timestamp)
        elif duration_hours is not None:
            expires_at = now_ts + int(duration_hours * 3600)
        elif duration_days is not None:
            expires_at = now_ts + int(duration_days * 86400)
        else:
            expires_at = now_ts + (30 * 86400)

    payload = {
        "license_version": 2,
        "device_id": hwid.strip().upper(),
        "client_name": client_name.strip(),
        "plan": plan.upper(),
        "expires_at": expires_at,
        "issued_at": now_ts,
        "license_id": f"LIC-{secrets.token_hex(6).upper()}"
    }

    # Strict compact canonical JSON
    payload_bytes = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode("utf-8")
    signature = priv_key.sign(payload_bytes)

    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")
    sig_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")

    token = f"SIGMA-LIC-{payload_b64}.{sig_b64}"
    return token, payload


def copy_to_clipboard(text: str) -> bool:
    """Copies output directly to Windows clipboard if available."""
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
                input=text,
                text=True,
                check=True,
                timeout=3
            )
            return True
    except Exception:
        pass
    return False


def interactive_cli():
    print("=" * 65)
    print("      مولّد المفاتيح والتراخيص الرسمي - SIGMA ASR VTT")
    print("               المطور: أصيل السويدي")
    print("=" * 65)
    print()

    client_name = input("1. اسم العميل أو المشتري (مثال: محمد علي): ").strip()
    if not client_name:
        client_name = "عميل معتمد"

    hwid = input("2. بصمة جهاز العميل (HWID) (مثال: SIGMA-XXXX-XXXX-XXXX-XXXX): ").strip()
    while not hwid:
        print("[-] تنبيه: بصمة الجهاز مطلوبة لربط البرنامج بجهاز العميل!")
        hwid = input("أدخل بصمة الجهاز (HWID): ").strip()

    print("\n3. نوع وصلاحية الترخيص:")
    print("   [1] مدى الحياة (Lifetime) - دائم بلا انتهاء")
    print("   [2] بالساعات (مثال: 12 ساعة، 24 ساعة، 48 ساعة، 72 ساعة)")
    print("   [3] بالأيام (مثال: 7 أيام، 30 يوماً، 365 يوماً)")
    print("   [4] تاريخ ووقت انتهاء محدد")
    choice = input("اختر رقم الخيار [الافتراضي: 1]: ").strip() or "1"

    license_type = "lifetime"
    hours = None
    days = None
    expiry_ts = None

    if choice == "2":
        license_type = "time_limited"
        h_str = input("أدخل عدد الساعات المسموح بها (مثال: 24 أو 48): ").strip()
        hours = float(h_str) if h_str else 24.0
    elif choice == "3":
        license_type = "time_limited"
        d_str = input("أدخل عدد الأيام المسموح بها (مثال: 30): ").strip()
        days = float(d_str) if d_str else 30.0
    elif choice == "4":
        license_type = "time_limited"
        date_str = input("أدخل تاريخ الانتهاء بصيغة YYYY-MM-DD HH:MM (مثال: 2026-12-31 23:59): ").strip()
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            expiry_ts = int(dt.timestamp())
        except Exception:
            print("[-] صيغة التاريخ غير صحيحة! سيتم اعتماد 30 يوماً افتراضياً.")
            days = 30.0

    plan = input("\n4. باقة الترخيص [PRO / VIP / ENTERPRISE] (الافتراضي: PRO): ").strip().upper() or "PRO"

    token, payload = generate_license_token(
        hwid=hwid,
        client_name=client_name,
        license_type=license_type,
        duration_hours=hours,
        duration_days=days,
        custom_expiry_timestamp=expiry_ts,
        plan=plan
    )

    print("\n" + "=" * 65)
    print("            تم توليد وتشفير المفتاح بنجاح!")
    print("=" * 65)
    print(f"اسم العميل:     {payload['client_name']}")
    print(f"بصمة الجهاز:    {payload['device_id']}")
    print(f"الباقة:         {payload['plan']}")
    print(f"رقم الترخيص:    {payload['license_id']}")
    if payload.get("expires_at") and payload["expires_at"] > 0:
        exp_dt = datetime.fromtimestamp(payload["expires_at"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"تاريخ الانتهاء: {exp_dt}")
    else:
        print("الصلاحية:       مدى الحياة (Lifetime)")
    
    print("\n--- كود المفتاح للنسخ والإرسال للعميل ---")
    print(token)
    print("------------------------------------------")

    if copy_to_clipboard(token):
        print("\n[+] تم نسخ كود المفتاح تلقائياً إلى الحافظة (Clipboard)!")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="SIGMA VTT Master License KeyGen")
    parser.add_argument("--hwid", type=str, help="Client Hardware ID (e.g. SIGMA-XXXX-XXXX-XXXX-XXXX)")
    parser.add_argument("--client", type=str, default="العميل المعتمد", help="Client Full Name")
    parser.add_argument("--hours", type=float, help="Duration in hours (e.g. 24 or 48)")
    parser.add_argument("--days", type=float, help="Duration in days (e.g. 30)")
    parser.add_argument("--lifetime", action="store_true", help="Generate permanent lifetime license")
    parser.add_argument("--plan", type=str, default="PRO", help="License plan (PRO, VIP, ENTERPRISE)")
    parser.add_argument("--print-public-key", action="store_true", help="Display embedded master public key hex")

    args = parser.parse_args()

    if args.print_public_key:
        priv = load_or_create_private_key()
        pub_raw = priv.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        print("MASTER PUBLIC KEY HEX:")
        print(pub_raw.hex())
        return

    if not args.hwid:
        interactive_cli()
        return

    license_type = "time_limited" if (args.hours or args.days) and not args.lifetime else "lifetime"
    token, payload = generate_license_token(
        hwid=args.hwid,
        client_name=args.client,
        license_type=license_type,
        duration_hours=args.hours,
        duration_days=args.days,
        plan=args.plan
    )

    print(token)


if __name__ == "__main__":
    main()
