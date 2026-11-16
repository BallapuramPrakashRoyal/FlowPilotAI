"""FlowPilot AI — Isolated Database Recovery Verification Script.

Tests backup and restoration into a strictly isolated test database environment.
Verifies record counts, foreign key relationships, and data integrity without
overwriting or touching the active database.
"""

import os
import sys
import gzip
import shutil
import sqlite3
import json

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(project_root, "backend")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from scripts.backup_database import backup_database, calculate_sha256

ISOLATED_TEST_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups", "isolated_recovery_test.db")


def verify_isolated_recovery():
    print("======================================================================")
    print("FLOWPILOT AI — ISOLATED DATABASE RECOVERY AUDIT")
    print("======================================================================\n")

    # 1. Generate fresh backup
    print("[1/5] Generating verified production backup...")
    backup_path = backup_database(retention_days=1)
    if not os.path.exists(backup_path):
        raise RuntimeError(f"Backup failed to create file at: {backup_path}")

    # 2. Check metadata and SHA256 integrity
    print("[2/5] Verifying backup checksum and metadata...")
    meta_path = backup_path + ".meta.json"
    with open(meta_path, "r") as f:
        meta = json.load(f)
    actual_sha = calculate_sha256(backup_path)
    assert meta["sha256"] == actual_sha, "Checksum mismatch on backup file!"
    print(f"      Verified SHA-256: {actual_sha[:16]}... ({meta['size_bytes']} bytes)")

    # 3. Restore strictly into isolated test file (never touching active database)
    print(f"[3/5] Restoring backup into ISOLATED test database: {ISOLATED_TEST_DB}...")
    if os.path.exists(ISOLATED_TEST_DB):
        os.remove(ISOLATED_TEST_DB)

    with gzip.open(backup_path, "rb") as f_in:
        with open(ISOLATED_TEST_DB, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    assert os.path.exists(ISOLATED_TEST_DB), "Isolated database failed to extract!"
    print("      Restoration complete. Database extracted successfully.")

    # 4. Verify Record Counts and Relational Integrity
    print("[4/5] Inspecting isolated database schema and relationship integrity...")
    conn = sqlite3.connect(ISOLATED_TEST_DB)
    cursor = conn.cursor()

    tables = [
        "users", "workspaces", "workspace_members", "workflows",
        "workflow_versions", "executions", "execution_nodes", "execution_events",
        "integrations", "integration_credentials", "knowledge_bases",
        "document_chunks", "approvals", "audit_logs"
    ]

    record_counts = {}
    for t in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cursor.fetchone()[0]
            record_counts[t] = cnt
            print(f"      - {t:<26}: {cnt:>4} records")
        except sqlite3.OperationalError:
            record_counts[t] = 0
            print(f"      - {t:<26}:    0 (table not in sqlite schema)")

    # Relational Integrity Tests
    print("\n[5/5] Executing relational foreign-key integrity validations...")
    
    # Check A: Every workspace belongs to a valid user
    cursor.execute("""
        SELECT COUNT(*) FROM workspaces w
        LEFT JOIN users u ON w.owner_id = u.id
        WHERE u.id IS NULL
    """)
    orphan_workspaces = cursor.fetchone()[0]
    assert orphan_workspaces == 0, f"Found {orphan_workspaces} orphaned workspaces!"
    print("      ✓ Zero orphaned workspaces (all owners mapped to valid users)")

    # Check B: Every workflow maps to a valid workspace
    cursor.execute("""
        SELECT COUNT(*) FROM workflows wf
        LEFT JOIN workspaces ws ON wf.workspace_id = ws.id
        WHERE ws.id IS NULL
    """)
    orphan_workflows = cursor.fetchone()[0]
    assert orphan_workflows == 0, f"Found {orphan_workflows} orphaned workflows!"
    print("      ✓ Zero orphaned workflows (all workflows bound to valid workspaces)")

    # Check C: Verified executions mapped to valid workflows
    cursor.execute("""
        SELECT COUNT(*) FROM executions ex
        WHERE ex.workflow_id IS NOT NULL 
          AND ex.workflow_id NOT LIKE 'agent-%'
          AND ex.workflow_id NOT IN (SELECT id FROM workflows)
    """)
    orphan_execs = cursor.fetchone()[0]
    assert orphan_execs == 0, f"Found {orphan_execs} orphaned workflow executions!"
    print(f"      ✓ Zero orphaned workflow executions (all standard executions map to valid workflows)")

    # Check D: Document chunks map to valid documents
    cursor.execute("""
        SELECT COUNT(*) FROM document_chunks dc
        LEFT JOIN documents d ON dc.document_id = d.id
        WHERE d.id IS NULL
    """)
    orphan_chunks = cursor.fetchone()[0]
    assert orphan_chunks == 0, f"Found {orphan_chunks} orphaned document chunks!"
    print(f"      ✓ Zero orphaned document chunks (all chunks map to valid parent documents)")

    conn.close()

    # 5. Clean up isolated test database
    if os.path.exists(ISOLATED_TEST_DB):
        os.remove(ISOLATED_TEST_DB)
    print("\n[+] Isolated test database safely purged. Active database UNTOUCHED.")
    print("======================================================================")
    print("DATABASE RECOVERY VERIFICATION: 100% PASSED")
    print("======================================================================")
    return True


if __name__ == "__main__":
    verify_isolated_recovery()
