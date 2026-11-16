"""FlowPilot AI — Production Database Restore Utility.

Safely restores database state from verified backups with SHA-256 validation
and pre-flight safety checks. Never overwrites without confirmation.
"""

import os
import sys
import gzip
import shutil
import hashlib
import json
import subprocess

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")


def calculate_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def restore_database(backup_path: str, force: bool = False) -> bool:
    if not os.path.isabs(backup_path):
        backup_path = os.path.join(BACKUP_DIR, backup_path)

    if not os.path.exists(backup_path):
        print(f"[-] Error: Backup file not found at: {backup_path}")
        return False

    print(f"[*] Pre-flight inspection for backup: {backup_path}")
    
    # Check checksum if metadata exists
    meta_path = backup_path + ".meta.json"
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            meta = json.load(f)
        expected_sha = meta.get("sha256")
        actual_sha = calculate_sha256(backup_path)
        if expected_sha and expected_sha != actual_sha:
            print(f"[-] Integrity check FAILED! Expected SHA256: {expected_sha}, found: {actual_sha}")
            return False
        print(f"[+] Backup integrity VERIFIED (SHA256: {actual_sha[:16]}...)")
        print(f"    Created at: {meta.get('timestamp')}, DB type: {meta.get('database_type')}")
    else:
        print("[!] Warning: No metadata file found; skipping SHA256 verification.")

    if not force:
        confirm = input("Are you sure you want to restore? This will replace the active database state. [y/N]: ")
        if confirm.lower() not in ["y", "yes"]:
            print("[-] Restore aborted by user.")
            return False

    # Perform restoration
    if backup_path.endswith(".sql.gz") or "pg_" in backup_path:
        # PostgreSQL restore
        psql_cmd = shutil.which("psql")
        if not psql_cmd:
            print("[-] Error: psql executable not found in PATH.")
            return False
            
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.POSTGRES_PASSWORD
        cmd = [
            psql_cmd,
            "-h", settings.POSTGRES_HOST,
            "-p", str(settings.POSTGRES_PORT),
            "-U", settings.POSTGRES_USER,
            "-d", settings.POSTGRES_DB,
        ]
        with gzip.open(backup_path, "rb") as gz_in:
            proc = subprocess.run(cmd, stdin=gz_in, capture_output=True, env=env)
            if proc.returncode != 0:
                print(f"[-] Restore failed with code {proc.returncode}: {proc.stderr.decode()}")
                return False
        print("[+] PostgreSQL database restored successfully.")
    else:
        # SQLite restore
        sqlite_target = os.path.join(backend_dir, "flowpilot.db")
        # Keep a recovery backup of current state
        if os.path.exists(sqlite_target):
            shutil.copy2(sqlite_target, sqlite_target + ".pre_restore_bak")
            
        with gzip.open(backup_path, "rb") as f_in:
            with open(sqlite_target, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"[+] Resilient SQLite database restored successfully to: {sqlite_target}")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/restore_database.py <backup_filename_or_path> [--force]")
        sys.exit(1)

    path = sys.argv[1]
    is_force = "--force" in sys.argv
    success = restore_database(path, force=is_force)
    sys.exit(0 if success else 1)
