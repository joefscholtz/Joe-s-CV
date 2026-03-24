import argparse
from pathlib import Path
import subprocess
from datetime import datetime
import sqlite3
from jinja2 import Environment, FileSystemLoader
from pypdf import PdfReader, PdfWriter
from db import Db


class ResumeFactory:
    def __init__(self, force_default_generation=False):
        self.db = Db()
        self.tex_dir = Path("tex")
        self.template_tex = self.tex_dir / "resume_template.tex"
        self.output_tex = self.tex_dir / "default_resume.tex"
        self.output_pdf = self.tex_dir / "default_resume.pdf"
        self.compressed_pdf = self.output_pdf.with_name(
            f"{self.output_pdf.stem}_compressed{self.output_pdf.suffix}"
        )
        self.jinja2env = Environment(
            block_start_string="((%",
            block_end_string="%))",
            variable_start_string="((",
            variable_end_string="))",
            comment_start_string="((#",
            trim_blocks=True,
            lstrip_blocks=True,
            comment_end_string="#))",
            loader=FileSystemLoader(str(self.tex_dir)),
        )
        self.jinja2_tex_template = self.jinja2env.get_template(
            str(self.template_tex.name)
        )
        if not self.check_for_changes() and not force_default_generation:
            print("─ No changes detected. Skipping default cv generation.")
        else:
            self.generate_default_cv()

    def check_for_changes(self):
        files_missing = not self.output_pdf.exists() or not self.compressed_pdf.exists()
        db_changed = self.db.check_for_changes()
        template_changed = self.db.check_for_changes([self.template_tex])

        return files_missing or db_changed or template_changed

    def get_default_cv(self):
        conn = self.db.get_conn()
        conn.row_factory = sqlite3.Row

        exp_cursor = conn.cursor()
        sub_cursor = conn.cursor()

        experiences = []
        exp_cursor.execute(
            "SELECT * FROM experiences WHERE is_default = 1 ORDER BY id ASC"
        )

        for exp in exp_cursor:
            exp_dict = dict(exp)
            exp_id = exp["id"]

            sub_cursor.execute(
                "SELECT text FROM descriptions WHERE exp_id=? AND is_default=1",
                (exp_id,),
            )
            exp_dict["description"] = " ".join([b[0] for b in sub_cursor.fetchall()])

            sub_cursor.execute(
                """
                SELECT s.name FROM skills s 
                JOIN experience_skills es ON s.id = es.skill_id 
                WHERE es.exp_id=? AND es.is_default=1""",
                (exp_id,),
            )
            exp_dict["skills"] = [s[0] for s in sub_cursor.fetchall()]

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

    def update_pdf_metadata(self, pdf_path, data):
        if not pdf_path.exists():
            print(f"✘ Failed to find PDF at {pdf_path}")
            return

        kw_str = ", ".join(data["keyword"])

        cmd = [
            "exiftool",
            "-overwrite_original",
            # --- Standard Info Dictionary ---
            f"-Title={data['title']}",
            f"-Author={data['creator']}",
            f"-Subject={data['description']}",
            f"-Keywords={kw_str}",
            # --- XMP Dublin Core (DC), Core Properties (CP / Adobe) ---
            f"-XMP-dc:Title={data['title']}",
            f"-XMP-dc:Creator={data['creator']}",
            f"-XMP-dc:Description={data['description']}",
            f"-XMP-dc:Subject={kw_str}",  # DC Subject is often used for keywords
            f"-XMP-pdf:Keywords={kw_str}",
            f"-XMP-xmp:Nickname={data['nickname']}",
            f"-Category={data['category']}",
            # --- DC/CP ---
            f"-DC:TITLE={data['title']}",
            f"-DC:CREATOR={data['creator']}",
            f"-CP:SUBJECT={kw_str}",
            f"-CP:KEYWORD={kw_str}",
            f"-CP:DESCRIPTION={data['description']}",
            f"-CP:CATEGORY={data['category']}",
            str(pdf_path.resolve()),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✔ Metadata synchronized (Info + XMP): {pdf_path.name}")
        except subprocess.CalledProcessError as e:
            print(f"✘ ExifTool failed: {e.stderr.decode()}")

    def generate_default_cv(self):
        experiences = self.get_default_cv()
        all_skills = set()
        for exp in experiences:
            all_skills.update(exp["skills"])

        keyword_list = sorted(list(all_skills))
        data = {
            "experiences": experiences,
            "title": "",
            "creator": "Joe Ferreira Scholtz",
            "nickname": "Joe",
            "keyword": keyword_list,
            "description": "",
            "category": "Resume",
        }
        self.generate_cv(data)

    def generate_cv(self, data):
        self.output_pdf.unlink(missing_ok=True)
        self.compressed_pdf.unlink(missing_ok=True)

        self.db.sync()

        rendered_tex = self.jinja2_tex_template.render(data)

        self.output_tex.write_text(rendered_tex)

        # Run lualatex twice for TikZ/geometry resolution
        for _ in range(2):
            subprocess.run(
                ["lualatex", "--interaction=nonstopmode", self.output_tex.name],
                cwd=str(self.tex_dir),
            )

        # Compress PDF
        subprocess.run(
            [
                "gs",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dPDFSETTINGS=/printer",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={self.compressed_pdf.resolve()}",
                str(self.output_pdf.resolve()),
            ],
            cwd=str(self.tex_dir),
            check=True,
        )
        self.update_pdf_metadata(self.output_pdf, data)
        self.update_pdf_metadata(self.compressed_pdf, data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CV builder utility.")
    parser.add_argument(
        "--force", action="store_true", help="Force default cv generation."
    )

    args = parser.parse_args()
    resume_factory = ResumeFactory(args.force)
