# Rust Justfile Recipes

## Template

```just
set dotenv-load

# The one command to run after every change.
default: build

# Canonical gate — autofix, then clippy, test, coverage. Compact output.
build: (_gate "fix")

# CI gate — identical checks, NO autofix. A clean run here == a clean CI.
ci: (_gate "check")

[private]
[no-exit-message]
[script("bash")]
_gate mode:
    set -uo pipefail
    step() { local n=$1; shift; local o
        if o=$("$@" 2>&1); then echo "✓ $n"
        else echo "✗ $n"; printf '%s\n' "$o"; exit 1; fi; }
    # Ratchet: fail below the committed .coverage-baseline; only `build` raises it.
    ratchet() {
        [[ $1 =~ ^[0-9]+(\.[0-9]+)?$ ]] || { echo "no coverage value: '$1'"; return 1; }
        local cur=$1 base
        base=$(cat .coverage-baseline 2>/dev/null || echo 0)
        awk -v c="$cur" -v b="$base" 'BEGIN{exit !(c>=b)}' ||
            { echo "Coverage regression: $cur% < $base%"; return 1; }
        if [ "{{mode}}" = "fix" ]; then echo "$cur" > .coverage-baseline; fi
    }
    if [ "{{mode}}" = "fix" ]; then
        step format cargo fmt --all
    else
        step format cargo fmt --all -- --check
    fi
    step clippy cargo clippy --all-targets --all-features -- -D warnings
    # cargo-llvm-cov runs the tests, enforces the floor, and writes the summary.
    step test cargo llvm-cov --all-features --workspace --fail-under-lines 80 --fail-under-functions 70 \
        --json --summary-only --output-path target/llvm-cov-summary.json
    step ratchet ratchet "$(jq '.data[0].totals.lines.percent' target/llvm-cov-summary.json)"

# Format code
fmt:
    cargo fmt --all

# Check formatting without modifying
fmt-check:
    cargo fmt --all -- --check

# Run clippy lints
clippy:
    cargo clippy --all-targets --all-features -- -D warnings

# Run tests
test *args:
    cargo test {{args}}

# Run tests with nextest (if installed)
test-fast *args:
    cargo nextest run {{args}}

# Compile debug (the gate already compiles via clippy/test — this is for a bare build)
compile:
    cargo build

# Build release artifact (not the gate — that's `build`)
release:
    cargo build --release

# Run the binary
run *args:
    cargo run -- {{args}}

# Generate and open docs
docs:
    cargo doc --open --no-deps

# Check MSRV
check-msrv:
    cargo msrv verify

# Update dependencies
update:
    cargo update

# Clean build artifacts
clean:
    cargo clean

# Watch mode (requires cargo-watch)
watch *args:
    cargo watch -x "test" -x "clippy" {{args}}

# Coverage report (requires cargo-llvm-cov, preferred over cargo-tarpaulin)
coverage:
    cargo llvm-cov --all-features --workspace --html
    @echo "Report: target/llvm-cov/html/index.html"

# Enforce coverage threshold (fails if below)
cov-check:
    cargo llvm-cov --all-features --workspace \
        --fail-under-lines 80 \
        --fail-under-functions 70
```

## Coverage notes

- **Per-file thresholds**: cargo-llvm-cov 0.8.6 and later support `--fail-under-file-lines <MIN>`. It fails when any file has line coverage below MIN, for example `cargo llvm-cov --workspace --fail-under-file-lines 70`. Older versions have no per-file gate; use the ratchet instead.
- **cargo-llvm-cov over cargo-tarpaulin**: faster, LLVM-native, better JSON/lcov output, and actively maintained. Use tarpaulin only if the project already depends on it.
- Commit `.coverage-baseline`. The `ci` gate fails when coverage drops below it, and the `build` gate raises it.

## Notes

- Prefer `cargo nextest` over `cargo test` if the project uses it — check for `.config/nextest.toml`
- For workspaces, add `--workspace` to test/clippy/build recipes
- If the project uses `cargo-make`, that's a different tool — migrate tasks to just recipes
- For binary crates, add `install` recipe: `cargo install --path .`
- For library crates, add `publish` recipe with `--dry-run` guard
