alias r := run
alias o:=open_default
alias z:=open_zathura

default:
  just --list

run +args="":
  uv run src/joe_s_cv/core/engine.py {{args}}

open_default:
  xdg-open ./tex/joe_fs_default_resume_compressed.pdf

open_zathura:
  zathura ./tex/joe_fs_default_resume.pdf

[no-cd]
remaining:
    #!/usr/bin/env bash
    find ./data/jobs -maxdepth 5 -type f -name "*.md" -print0 | while IFS= read -r -d '' f; do
        # Remove the leading ./ for cleaner output
        clean_f="${f#./}"
        if [[ ! -f "${clean_f%.md}.json" ]]; then
            echo "$clean_f"
        fi
    done

[no-cd]
pick:
    #!/usr/bin/env bash
    remaining_files=$(just remaining)
    
    if [ -z "$remaining_files" ]; then
      echo "No .md remaining"
      exit 0
    fi

    selected=$(echo "$remaining_files" | gum filter \
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

# export PYTHONPATH=$PYTHONPATH:$(pwd)/src && uv run python src/joe_s_cv/app/main.py {{args}}
app +args="":
  uv run python src/joe_s_cv/app/main.py {{args}}
