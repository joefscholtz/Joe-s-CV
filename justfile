alias r := run
alias o:=open_default
alias z:=open_zathura

default:
  just --list

run +args="":
  uv run src/joe-s-cv/process_cv.py {{args}}

open_default:
  xdg-open ./tex/joe_fs_default_resume_compressed.pdf

open_zathura:
  zathura ./tex/joe_fs_default_resume.pdf

[no-cd]
remaining:
    #!/usr/bin/env bash
    find . -maxdepth 1 -type f -name "*.md" -print0 | while IFS= read -r -d '' f; do
        # Remove the leading ./ for cleaner output
        clean_f="${f#./}"
        if [[ ! -f "${clean_f%.md}.json" ]]; then
            echo "$clean_f"
        fi
    done

[no-cd]
pick:
    #!/usr/bin/env bash
    selected=$(just remaining | gum filter \
        --placeholder "Select Job Description..." \
        --header "Navigate: Ctrl+n (Down) / Ctrl+p (Up)" \
        --indicator "➜" \
        --match.foreground "210")
    
    if [ -n "$selected" ]; then
        echo "── Tailoring CV for: $selected"
        just run --jd "{{invocation_directory()}}/$selected"
    else
        echo "✘ No file selected."
    fi
