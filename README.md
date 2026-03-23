# Joe's CV

My LaTeX Curriculum Vitae builder.

```
.
├── data
│   ├── schema.yaml                 	# Sqlite database architeture
│   ├── table_descriptions.yaml     	# Data for the table descriptions
│   ├── table_experience_skills.yaml	# Junction table between experiences and skills
│   ├── table_experiences.yaml      	# Data for the table experiences
│   └── table_skils.yaml            	# Data for the table skills
├── tex
│   ├── fonts                       	# Fonts used in the LaTeX generation
│   ├── pictures                    	# Images used in the LaTeX generation
│   ├── default_resume.tex          	# Generated default resume
│   └── resume_template.tex         	# LaTex template using Jinja2
├── justfile                        	# Recepies
├── main.py                         	# Latex document generation from template
└── sync_data.py                    	# Sqlite database creation and synchronization
```

## Prerequisites

- lualatex
- uv
- just (Optional)

## Usage

```bash
uv run sync_data.py
uv run main.py
```

or using just `just run`.
