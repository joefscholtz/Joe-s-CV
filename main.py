import subprocess
from datetime import datetime
import sqlite3
from jinja2 import Environment, FileSystemLoader
from pypdf import PdfReader, PdfWriter

# Custom delimiters to avoid LaTeX conflict
env = Environment(
    block_start_string="((%",
    block_end_string="%))",
    variable_start_string="((",
    variable_end_string="))",
    comment_start_string="((#",
    trim_blocks=True,
    lstrip_blocks=True,
    comment_end_string="#))",
    loader=FileSystemLoader("tex"),
)


def get_default_cv():
    conn = sqlite3.connect("data/cv_database.db")
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
            datetime.strptime(
                x["start_date"],
                "%b %Y",
            ),
        ),
        reverse=True,
    )

    return experiences


if __name__ == "__main__":
    data = {"experiences": get_default_cv()}
    tex = env.get_template("resume_template.tex").render(data)

    with open("tex/default_resume.tex", "w") as f:
        f.write(tex)
    subprocess.run(
        [
            "lualatex",
            "--interaction=nonstopmode",
            "default_resume.tex",
        ],
        cwd="tex",
    )
