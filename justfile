alias r := run
alias o:=open_default
alias z:=open_zathura

default:
  just --list

run args="":
  uv run src/joe-s-cv/process_cv.py {{args}}

open_default:
  xdg-open ./tex/default_resume_compressed.pdf

open_zathura:
  zathura ./tex/default_resume.pdf
