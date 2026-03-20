import yaml
import sqlite3
import hashlib
import os
import sys

# Ensure this path is correct and the 'data' folder exists
CACHE_FILE = "data/.sync_cache"
DB_PATH = "data/cv_database.db"


def get_file_hash(filepath):
    """Generates an MD5 hash of a file to detect changes."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def check_for_changes(files):
    """Returns True if any file hash has changed since the last sync."""
    # Ensure directory exists so cache can be written
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    current_hashes = {f: get_file_hash(f) for f in files}

    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "w") as f:
            yaml.dump(current_hashes, f)
        return True

    with open(CACHE_FILE, "r") as f:
        old_hashes = yaml.safe_load(f) or {}

    if current_hashes != old_hashes:
        with open(CACHE_FILE, "w") as f:
            yaml.dump(current_hashes, f)
        return True
    return False


def sync():
    data_files = [
        "data/schema.yaml",
        "data/table_experiences.yaml",
        "data/table_descriptions.yaml",
        "data/table_skills.yaml",
        "data/table_experience_skills.yaml",
    ]

    if not check_for_changes(data_files):
        print("─ No changes detected in YAML files. Skipping sync.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # CRITICAL: Turn off constraints ONLY during the drop/rebuild phase
    cursor.execute("PRAGMA foreign_keys = OFF;")

    try:
        cursor.execute("BEGIN TRANSACTION;")

        with open("data/schema.yaml", "r") as f:
            schema_config = yaml.safe_load(f)
            tables = schema_config["tables"]

            # 1. Drop tables (Reverse order is safer, but OFF handles it)
            for table_name in tables.keys():
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

            # 2. Recreate tables
            for table_name, details in tables.items():
                cols = [f"{n} {d}" for n, d in details["columns"].items()]
                fks = details.get("foreign_keys", [])
                cursor.execute(f"CREATE TABLE {table_name} ({', '.join(cols + fks)})")

        # 3. Load Data
        for file_path in data_files:
            if "schema.yaml" in file_path:
                continue
            table_name = file_path.replace("data/table_", "").replace(".yaml", "")

            if not os.path.exists(file_path):
                continue

            with open(file_path, "r") as f:
                rows = yaml.safe_load(f)
                if not rows:
                    continue
                for row in rows:
                    cols = ", ".join(row.keys())
                    placeholders = ", ".join(["?"] * len(row))
                    cursor.execute(
                        f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})",
                        list(row.values()),
                    )

        # 4. RE-ENABLE and CHECK constraints before committing
        cursor.execute("PRAGMA foreign_keys = ON;")
        # This triggers a check on all existing data
        cursor.execute("PRAGMA foreign_key_check;")
        errors = cursor.fetchall()

        if errors:
            raise sqlite3.IntegrityError(f"Foreign key violations found: {errors}")

        conn.commit()
        print("✔ Database successfully synced and validated.")

    except Exception as e:
        conn.rollback()
        print(f"✘ SYNC FAILED: {e}")
        # Wipe cache so we force a retry after user fixes the YAML
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    sync()
