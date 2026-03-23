alias r := run
alias o:=open_default
alias z:=open_zathura

default:
  just --list

run:
  uv run sync_data.py
  uv run main.py

open_default:
  xdg-open ./tex/default_resume.pdf

open_zathura:
  zathura ./tex/default_resume.pdf
