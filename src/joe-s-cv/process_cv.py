from pathlib import Path
import subprocess
from datetime import datetime
import sqlite3
from jinja2 import Environment, FileSystemLoader
from pypdf import PdfReader, PdfWriter
from db import Db


def get_default_cv(db):
    conn = db.get_conn()
    conn.row_factory = sqlite3.Row

    exp_cursor = conn.cursor()
    sub_cursor = conn.cursor()

    experiences = []
    exp_cursor.execute("SELECT * FROM experiences WHERE is_default = 1 ORDER BY id ASC")

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


def update_pdf_metadata(pdf_path, metadata):
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


if __name__ == "__main__":
    text_dir = Path("tex")
    output_tex = text_dir / "default_resume.tex"
    output_pdf = text_dir / "default_resume.pdf"
    compressed_pdf = output_pdf.with_name(
        f"{output_pdf.stem}_compressed{output_pdf.suffix}"
    )
    db = Db()
    db.sync()

    data = {"experiences": get_default_cv(db)}

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
        loader=FileSystemLoader(str(text_dir)),
    )

    tex_template = jinja2env.get_template("resume_template.tex")
    rendered_tex = tex_template.render(data)

    output_tex.write_text(rendered_tex)

    # Run lualatex twice for TikZ/geometry resolution
    for _ in range(2):
        subprocess.run(
            ["lualatex", "--interaction=nonstopmode", output_tex.name],
            cwd=str(text_dir),
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
            f"-sOutputFile={compressed_pdf.name}",
            output_pdf.name,
        ],
        cwd=str(text_dir),
        check=True,
    )

    # update_pdf_metadata(
    #     output_pdf,
    #     {
    #     "DC: TITLE": "", # target job title
    #     "DC: CREATOR": "Joe Ferreira Scholtz",
    #     "CP: KEYWORD": "",
    #     "CP: DESCRIPTION": "", # short version of the target job description
    #     "CP: CATEGORY": "Resume",
    #     }
    # )
