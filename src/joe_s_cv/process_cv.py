import argparse
from pathlib import Path
import subprocess
from datetime import datetime
import json
import sqlite3
from jinja2 import Environment, FileSystemLoader
from db import Db
from ai_assistant import AIAssistant
from camel_converter import to_snake


class ResumeFactory:
    def __init__(
        self, force_default_generation=False, jd_path=None, use_previous_result=False
    ):
        self.db = Db()

        self.tex_dir = Path("tex")
        self.template_tex = self.tex_dir / "resume_template.tex"
        self.output_tex = self.tex_dir / "joe_fs_default_resume.tex"
        self.output_pdf = self.output_tex.with_name(f"{self.output_tex.stem}.pdf")
        self.compressed_pdf = self.output_pdf.with_name(
            f"{self.output_pdf.stem}_compressed{self.output_pdf.suffix}"
        )

        self.use_previous_result = use_previous_result

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
            self.db.sync()
            self.generate_default_cv()
        if jd_path:
            self.db.sync()
            print(f"── Tailoring CV for: {jd_path}")
            self.generate_tailored_cv(Path(jd_path))

    def check_for_changes(self):
        files_missing = not self.output_pdf.exists() or not self.compressed_pdf.exists()
        db_changed = self.db.check_for_changes()
        template_changed = self.db.check_for_changes([self.template_tex])

        return files_missing or db_changed or template_changed

    def get_default_cv(self):
        all_exp = self.db.get_experiences()
        default_list = []

        for exp in all_exp:
            if exp.get("is_default") == 1:
                exp["description"] = " ".join(
                    [d["text"] for d in exp["descriptions"] if d["is_default"] == 1]
                )

                exp["skills"] = [
                    s["name"] for s in exp["skills"] if s["is_default"] == 1
                ]

                default_list.append(exp)
        return default_list

    def generate_tailored_cv(self, jd_path):
        ai = AIAssistant()

        raw_pool = self.db.get_experiences()

        ai_pool = []
        for exp in raw_pool:
            ai_pool.append(
                {
                    "id": exp["id"],
                    "role": exp["role"],
                    "company": exp["company"],
                    "descriptions": [
                        {"id": d["id"], "text": d["text"]} for d in exp["descriptions"]
                    ],
                    "skills": [
                        {"id": s["id"], "name": s["name"]} for s in exp["skills"]
                    ],
                }
            )

        plan = ai.analyze_job(jd_path, json.dumps(ai_pool), self.use_previous_result)

        experiences = self.db.get_tailored_experiences(plan["selected_experiences"])

        for exp in experiences:
            for word in plan["highlights"]:
                # Highlighting descriptions
                if word in exp["description"]:
                    exp["description"] = exp["description"].replace(
                        word, f"\\highlight{{{word}}}"
                    )

                exp["skills"] = [
                    s.replace(word, f"\\highlight{{{word}}}") if word in s else s
                    for s in exp["skills"]
                ]

        plan["company"] = to_snake(plan["company"])

        data = {
            "experiences": experiences,
            "title": plan["title"],
            "creator": "Joe Ferreira Scholtz",
            "nickname": "Joe",
            "keyword": plan["highlights"],
            "description": plan["description"],
            "category": "Resume",
        }

        company_dir = self.tex_dir / "companies" / f"{plan["company"]}"
        company_dir.mkdir(parents=True, exist_ok=True)

        output_tex = company_dir / f"joe_fs_resume_{Path(jd_path).stem}.tex"
        output_pdf = output_tex.with_name(f"{output_tex.stem}.pdf")
        compressed_pdf = output_pdf.with_name(
            f"{output_pdf.stem}_compressed{output_pdf.suffix}"
        )

        self.generate_cv(
            data,
            output_tex=output_tex,
            output_pdf=output_pdf,
            compressed_pdf=compressed_pdf,
            use_double_degree_tcolorbox=False,
            parent_dir=company_dir,
        )

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
            f"-XMP-cp:Description={data['description']}",
            f"-XMP-dc:Subject={kw_str}",  # DC Subject is often used for keywords
            f"-XMP-cp:Subject={kw_str}",  # DC Subject is often used for keywords
            f"-XMP-pdf:Keywords={kw_str}",
            f"-XMP-cp:Keywords={kw_str}",
            f"-XMP-xmp:Nickname={data['nickname']}",
            f"-Category={data['category']}",
            f"-XMP-cp:Category={data['category']}",
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
        self.generate_cv(data, use_double_degree_tcolorbox=True)

    def generate_cv(
        self,
        data,
        output_tex=None,
        output_pdf=None,
        compressed_pdf=None,
        use_double_degree_tcolorbox=True,
        parent_dir=None,
    ):
        if parent_dir is None:
            parent_dir = self.tex_dir
        else:
            dest_fonts_dir = parent_dir / "fonts"
            dest_fonts_dir.mkdir(exist_ok=True)

            src_fonts_dir = self.tex_dir / "fonts"
            if src_fonts_dir.exists():
                for src_file in src_fonts_dir.glob("*"):
                    if src_file.is_file():
                        dest_file = dest_fonts_dir / src_file.name
                        if not dest_file.exists():
                            dest_file.write_bytes(src_file.read_bytes())

        abs_tex_dir = self.tex_dir.resolve()
        abs_parent_dir = parent_dir.resolve()

        try:
            # relative_to only works 'downwards', so we use it to find the depth
            depth = len(abs_parent_dir.relative_to(abs_tex_dir).parts)
            # Create a string like "../../"
            parent_prefix = "../" * depth
        except ValueError:
            # If parent_dir is NOT a subdirectory of tex_dir (e.g. they are the same)
            parent_prefix = ""
        if output_tex is None:
            output_tex = self.output_tex
        if output_pdf is None:
            output_pdf = self.output_pdf
        if compressed_pdf is None:
            compressed_pdf = self.compressed_pdf
        output_pdf.unlink(missing_ok=True)
        compressed_pdf.unlink(missing_ok=True)

        self.db.sync()

        experiences = data["experiences"]
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
        data["experiences"] = experiences
        data["parent_prefix"] = parent_prefix
        data["use_double_degree_tcolorbox"] = use_double_degree_tcolorbox

        rendered_tex = self.jinja2_tex_template.render(data)

        output_tex.write_text(rendered_tex)

        # Run lualatex twice for TikZ/geometry resolution
        for _ in range(2):
            subprocess.run(
                ["lualatex", "--interaction=nonstopmode", output_tex.name],
                cwd=str(parent_dir),
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
                f"-sOutputFile={compressed_pdf.resolve()}",
                str(output_pdf.resolve()),
            ],
            cwd=str(parent_dir),
            check=True,
        )
        self.update_pdf_metadata(output_pdf, data)
        self.update_pdf_metadata(compressed_pdf, data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CV builder utility.")
    parser.add_argument(
        "--force", action="store_true", help="Force default cv generation."
    )
    parser.add_argument(
        "--jd", type=str, default=None, help="Path to job description file."
    )
    parser.add_argument(
        "--use_previous_result",
        action="store_true",
        help="Use previous json dump result instead of recomputing with AI",
    )

    args = parser.parse_args()
    resume_factory = ResumeFactory(args.force, args.jd, args.use_previous_result)
