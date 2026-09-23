# Canonical local quality commands.
default: build
build: (_gate "fix")
ci: (_gate "check")

[private]
[no-exit-message]
[script("bash")]
_gate mode:
    set -uo pipefail
    export PYTHONDONTWRITEBYTECODE=1
    step() { local name=$1; shift; local output
        if output="$("$@" 2>&1)"; then echo "✓ $name"
        else echo "✗ $name"; printf '%s\n' "$output"; exit 1; fi
    }
    if [ "{{mode}}" = "fix" ]; then
        step markdown-fix markdownlint-cli2 --fix "**/*.md" "#.cheese/**" "#.cache/**" "#.context/**" "#.serena/**"
        step yaml-fix yamlfmt .
    else
        step markdown markdownlint-cli2 "**/*.md" "#.cheese/**" "#.cache/**" "#.context/**" "#.serena/**"
        step yaml yamlfmt -lint .
    fi
    step yaml-lint yamllint -c .yamllint.yml .
    step tests python3 .github/scripts/test_validate_skills.py
    step hook-tests python3 .github/scripts/test_check_hooks.py
    step eval-tests python3 .github/scripts/test_validate_evals.py
    step template-tests python3 .github/scripts/test_templates.py
    step skills python3 .github/scripts/validate_skills.py
    step evals python3 .github/scripts/validate_evals.py
    if [ "{{mode}}" = "fix" ]; then
        step prek prek run --all-files
    else
        step hooks python3 .github/scripts/check_hooks.py
    fi

list:
    @just --list
