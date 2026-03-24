from pathlib import Path
import yaml
import sqlite3
import hashlib
import sys


class Db:
    def __init__(self):
        self.cache_file = Path("data/.sync_cache")
        self.db_path = Path("data/cv_database.db")
        self.data_files = [
            Path("data/schema.yaml"),
            Path("data/table_experiences.yaml"),
            Path("data/table_descriptions.yaml"),
            Path("data/table_skills.yaml"),
            Path("data/table_experience_skills.yaml"),
        ]

    def get_file_hash(self, filepath):
        """Generates an MD5 hash of a file to detect changes."""
        if not filepath.exists():
            return None
        return hashlib.md5(filepath.read_bytes()).hexdigest()

    def check_for_changes(self, files=None):
        """Returns True if any file hash has changed since the last sync."""
        if files is None:
            files = self.data_files

        if not self.db_path.is_file():
            return True

        # Ensure 'data' directory exists
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        current_hashes = {str(f): self.get_file_hash(f) for f in files}

        if not self.cache_file.exists():
            self.cache_file.write_text(yaml.dump(current_hashes))
            return True

        old_hashes = yaml.safe_load(self.cache_file.read_text()) or {}

        if current_hashes != old_hashes:
            self.cache_file.write_text(yaml.dump(current_hashes))
            return True
        return False

    def get_conn(self):
        return sqlite3.connect(self.db_path)

    def sync(self):
        if not self.check_for_changes():
            print("─ No changes detected in YAML files. Skipping sync.")
            return

        conn = self.get_conn()  # Fixed: added parentheses
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys = OFF;")

        try:
            cursor.execute("BEGIN TRANSACTION;")

            schema_path = Path("data/schema.yaml")
            schema_config = yaml.safe_load(schema_path.read_text())
            tables = schema_config["tables"]

            # 1. Rebuild Schema
            for table_name in tables.keys():
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

            for table_name, details in tables.items():
                cols = [f"{n} {d}" for n, d in details["columns"].items()]
                fks = details.get("foreign_keys", [])
                cursor.execute(f"CREATE TABLE {table_name} ({', '.join(cols + fks)})")

            # 2. Load Data
            for file_path in self.data_files:
                if "schema.yaml" in file_path.name:
                    continue

                # Table name discovery based on filename
                table_name = file_path.name.replace("table_", "").replace(".yaml", "")

                if not file_path.exists():
                    continue

                rows = yaml.safe_load(file_path.read_text())
                if not rows:
                    continue

                for row in rows:
                    cols = ", ".join(row.keys())
                    placeholders = ", ".join(["?"] * len(row))
                    cursor.execute(
                        f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})",
                        list(row.values()),
                    )

            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("PRAGMA foreign_key_check;")
            errors = cursor.fetchall()

            if errors:
                raise sqlite3.IntegrityError(f"Foreign key violations found: {errors}")

            conn.commit()
            print("✔ Database successfully synced and validated.")

        except Exception as e:
            conn.rollback()
            print(f"✘ SYNC FAILED: {e}")
            if self.cache_file.exists():
                self.cache_file.unlink()
            sys.exit(1)
        finally:
            conn.close()


if __name__ == "__main__":
    db = Db()
    db.sync()
