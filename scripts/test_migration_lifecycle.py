"""Rigorous verification of Alembic migration lifecycle on an isolated database."""

import os
import sys
import sqlite3
from sqlalchemy import create_engine, inspect

# Ensure backend is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(project_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from alembic import command
from alembic.config import Config
from app.core.database import Base
import app.database.models

test_db_path = os.path.join(project_root, "backups", "isolated_mig_test.db")


def run_lifecycle_test():
    # Clean any leftover
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    sync_url = f"sqlite:///{test_db_path}"
    print(f"Testing isolated migration lifecycle on: {sync_url}")

    # Set up Alembic config
    cfg_path = os.path.join(project_root, "alembic.ini")
    cfg = Config(cfg_path)
    cfg.set_main_option("sqlalchemy.url", sync_url)

    # 1. Check current is empty
    print("\n--- Step 1: Check baseline is empty ---")
    conn = sqlite3.connect(test_db_path)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()
    assert len(tables) == 0, f"Expected 0 tables, found {tables}"
    print("PASS: Baseline database is completely empty.")

    # 2. Upgrade to baseline: 1a2b3c4d5e6f
    print("\n--- Step 2: Upgrade to baseline revision (1a2b3c4d5e6f) ---")
    command.upgrade(cfg, "1a2b3c4d5e6f")

    engine = create_engine(sync_url)
    insp = inspect(engine)
    table_names = set(insp.get_table_names())
    assert "agent_runs" in table_names, "agent_runs missing!"
    assert "users" in table_names, "users missing!"
    assert len(table_names) >= 20, f"Expected >= 20 tables, got {len(table_names)}"

    cols_agent_runs = {c["name"] for c in insp.get_columns("agent_runs")}
    assert "execution_id" not in cols_agent_runs, "execution_id should not exist in baseline agent_runs"
    print(f"PASS: Baseline created {len(table_names)} tables. agent_runs has {len(cols_agent_runs)} baseline columns.")

    # 3. Upgrade to head: f675da0e0729
    print("\n--- Step 3: Upgrade to head revision (f675da0e0729) ---")
    command.upgrade(cfg, "head")

    engine.dispose()
    engine = create_engine(sync_url)
    insp = inspect(engine)
    cols_agent_runs_head = {c["name"] for c in insp.get_columns("agent_runs")}
    expected_m6_cols = {
        "execution_id", "task_id", "task_input", "task_output",
        "handoff_data", "retry_count", "provider", "model",
        "error_message", "validation_findings", "approval_status",
        "idempotency_key"
    }
    missing = expected_m6_cols - cols_agent_runs_head
    assert not missing, f"Missing columns in agent_runs at head: {missing}"
    print(f"PASS: Upgraded to head. agent_runs has all {len(cols_agent_runs_head)} columns including all Milestone 6 fields.")

    # 4. Downgrade to 1a2b3c4d5e6f
    print("\n--- Step 4: Downgrade to 1a2b3c4d5e6f ---")
    command.downgrade(cfg, "1a2b3c4d5e6f")

    engine.dispose()
    engine = create_engine(sync_url)
    insp = inspect(engine)
    cols_reverted = {c["name"] for c in insp.get_columns("agent_runs")}
    assert "execution_id" not in cols_reverted, "execution_id should be removed on downgrade"
    print(f"PASS: Downgrade successful. agent_runs reverted to {len(cols_reverted)} baseline columns.")

    # 5. Downgrade to base
    print("\n--- Step 5: Downgrade to base ---")
    command.downgrade(cfg, "base")

    engine.dispose()
    conn = sqlite3.connect(test_db_path)
    remaining_tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version'").fetchall()]
    conn.close()
    assert len(remaining_tables) == 0, f"Expected 0 tables after downgrade base, found: {remaining_tables}"
    print("PASS: Downgrade to base dropped all application tables cleanly.")

    # 6. Re-upgrade from base to head in a single step
    print("\n--- Step 6: Full re-upgrade from base to head ---")
    command.upgrade(cfg, "head")

    engine = create_engine(sync_url)
    insp = inspect(engine)
    final_tables = set(insp.get_table_names())
    assert "users" in final_tables
    assert "agent_runs" in final_tables
    cols_final = {c["name"] for c in insp.get_columns("agent_runs")}
    assert not (expected_m6_cols - cols_final)
    print(f"PASS: Fresh re-upgrade from base to head succeeded! {len(final_tables)} tables present.")
    engine.dispose()

    # Clean up
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    print("\nALL ALEMBIC MIGRATION LIFECYCLE CHECKS PASSED 100%!")


if __name__ == "__main__":
    run_lifecycle_test()
