from pathlib import Path
from datetime import datetime
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
        if files is None:
            files = self.data_files

        if not self.db_path.is_file():
            return True

        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # 1. Load existing cache
        old_hashes = {}
        if self.cache_file.exists():
            try:
                old_hashes = yaml.safe_load(self.cache_file.read_text()) or {}
            except yaml.YAMLError:
                old_hashes = {}

        # 2. Calculate current hashes for the requested files
        current_hashes = {str(f.resolve()): self.get_file_hash(f) for f in files}

        # 3. Determine if anything in THIS set has changed
        changed = False
        for filepath, h in current_hashes.items():
            if old_hashes.get(filepath) != h:
                changed = True
                old_hashes[filepath] = h  # Update the local dictionary

        # 4. If changed, write the MERGED dictionary back to disk
        if changed:
            self.cache_file.write_text(yaml.dump(old_hashes))
            return True

        return False

    def get_conn(self):
        return sqlite3.connect(self.db_path)

    def sync(self):
        if not self.check_for_changes():
            print("─ No changes detected in YAML files. Skipping sync.")
            return

        conn = self.get_conn()
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

    def get_experiences(self):
        conn = self.get_conn()
        conn.row_factory = sqlite3.Row
        exp_cursor = conn.cursor()
        sub_cursor = conn.cursor()

        experiences = []
        exp_cursor.execute("SELECT * FROM experiences ORDER BY id ASC")

        for exp in exp_cursor:
            exp_dict = dict(exp)
            exp_id = exp["id"]

            sub_cursor.execute(
                "SELECT id, text, is_default FROM descriptions WHERE exp_id=?",
                (exp_id,),
            )
            exp_dict["descriptions"] = [dict(row) for row in sub_cursor.fetchall()]

            sub_cursor.execute(
                """
                SELECT s.id, s.name, es.is_default FROM skills s 
                JOIN experience_skills es ON s.id = es.skill_id 
                WHERE es.exp_id=?""",
                (exp_id,),
            )
            exp_dict["skills"] = [dict(row) for row in sub_cursor.fetchall()]

            experiences.append(exp_dict)

        conn.close()

        experiences.sort(
            key=lambda x: (
                1 if x["end_date"] == "Present" else 0,
                datetime.strptime(x["start_date"], "%b %Y"),
            ),
            reverse=True,
        )
        return experiences

    def get_experiences_by_id(self, exp_ids):
        experiences = self.get_experiences()
        matched_experiences = []
        for exp in experiences:
            if exp["id"] in exp_ids:
                matched_experiences.append(exp)
        return matched_experiences

    def get_tailored_experiences(self, selected_plan):
        all_pool = self.get_experiences()
        tailored_list = []
        pool_map = {str(exp["id"]): exp for exp in all_pool}

        for selection in selected_plan:
            exp_id = str(selection["experience_id"])
            if exp_id in pool_map:
                base_exp = pool_map[exp_id].copy()

                base_exp["description"] = " ".join(
                    [
                        d["text"]
                        for d in base_exp["descriptions"]
                        if d["id"] in selection["descriptions_ids"]
                    ]
                )

                base_exp["skills"] = [
                    s["name"]
                    for s in base_exp["skills"]
                    if s["id"] in selection["skills_ids"]
                ]

                tailored_list.append(base_exp)
        return tailored_list


if __name__ == "__main__":
    db = Db()
    db.sync()
