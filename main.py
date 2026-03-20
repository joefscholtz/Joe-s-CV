import subprocess
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
    comment_end_string="#))",
    loader=FileSystemLoader("tex"),
)


def get_default_cv():
    conn = sqlite3.connect("data/cv_database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    experiences = []
    for exp in cursor.execute("SELECT * FROM experiences"):
        exp_dict = dict(exp)
        # Fetch default bullets
        bullets = cursor.execute(
            "SELECT text FROM descriptions WHERE exp_id=? AND is_default=1",
            (exp["id"],),
        )
        exp_dict["bullets"] = [b[0] for b in bullets]
        # Fetch default skills
        skills = cursor.execute(
            """
            SELECT s.name FROM skills s 
            JOIN experience_skills es ON s.id = es.skill_id 
            WHERE es.exp_id=? AND es.is_default=1""",
            (exp["id"],),
        )
        exp_dict["skills"] = [s[0] for s in skills]
        experiences.append(exp_dict)
    return experiences


# 1. Fetch Data -> 2. Render Template -> 3. Compile -> 4. Metadata
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
