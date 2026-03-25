# Joe's CV

My LaTeX Curriculum Vitae builder.

```
.
├── data/
│   ├── schema.yaml                 	# Sqlite database architeture
│   ├── table_descriptions.yaml     	# Data for the table descriptions
│   ├── table_experience_skills.yaml	# Junction table between experiences and skills
│   ├── table_experiences.yaml      	# Data for the table experiences
│   └── table_skils.yaml            	# Data for the table skills
├── src/joe-s-cv/
│   ├── process_cv.py               	# Latex document generation from template
│   └── db.py                       	# Sqlite database creation and synchronization
├── tex/
│   ├── fonts                       	# Fonts used in the LaTeX generation
│   ├── pictures                    	# Images used in the LaTeX generation
│   ├── default_resume.tex          	# Generated default resume
│   └── resume_template.tex         	# LaTex template using Jinja2
└── justfile                        	# Recepies
```

## Prerequisites

- lualatex
- Ghostscript
- exiftool
- uv
- just (Optional)
- Zhatura (Optional)

## Usage

```bash
uv run src/joe-s-cv/process_cv.py
```

or using just `just run`.

## TODOs

[ ] Add the option to rerun without using the previous output for that job description file
[ ] Flag to hide the Double Degree `tcolorbox`
