alias r := run
alias o:=open_default

default:
  just --list

run:
  uv run sync_data.py
  uv run main.py

open_default:
  xdg-open ./tex/default_resume.pdf

