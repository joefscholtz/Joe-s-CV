from pathlib import Path
import subprocess
from datetime import datetime
import sqlite3
from jinja2 import Environment, FileSystemLoader
from pypdf import PdfReader, PdfWriter
from db import Db


class ResumeFactory:
    def __init__(self):
        self.db = Db()
        self.tex_dir = Path("tex")
        self.template_tex = self.tex_dir / "resume_template.tex"
        self.output_tex = self.tex_dir / "default_resume.tex"
        self.output_pdf = self.tex_dir / "default_resume.pdf"
        self.compressed_pdf = self.output_pdf.with_name(
            f"{self.output_pdf.stem}_compressed{self.output_pdf.suffix}"
        )

    def check_for_changes(self):
        return (
            (not self.output_pdf.is_file())
            or (not self.compressed_pdf.is_file())
            or self.db.check_for_changes()
            or self.db.check_for_changes([self.template_tex])
        )

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
                "SELECT * FROM descriptions WHERE exp_id=? AND is_default=1",
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

    def update_pdf_metadata(self, pdf_path, metadata):
        if not pdf_path.exists():
            print(f"✘ Failed to find PDF at {pdf_path}")
            return

        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.add_metadata(metadata)

        with pdf_path.open("wb") as f:
            writer.write(f)

        print(f"✔ Metadata updated: {str(pdf_path)}")

    def generate_default_cv(self):
        self.db.sync()

        data = {"experiences": self.get_default_cv()}

        # Jinja2 setup with Path
        jinja2env = Environment(
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

        jinja2_tex_template = jinja2env.get_template(self.template_tex)
        rendered_tex = jinja2_tex_template.render(data)

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
                f"-sOutputFile={self.compressed_pdf.name}",
                self.output_pdf.name,
            ],
            cwd=str(self.tex_dir),
            check=True,
        )

        # update_pdf_metadata(
        #     self.output_pdf,
        #     {
        #     "DC: TITLE": "", # target job title
        #     "DC: CREATOR": "Joe Ferreira Scholtz",
        #     "CP: KEYWORD": "",
        #     "CP: DESCRIPTION": "", # short version of the target job description
        #     "CP: CATEGORY": "Resume",
        #     }
        # )


if __name__ == "__main__":
    resume_factory = ResumeFactory()
    if not resume_factory.check_for_changes():
        print("─ No changes detected. Skipping default cv generation.")
    else:
        resume_factory.generate_default_cv()
