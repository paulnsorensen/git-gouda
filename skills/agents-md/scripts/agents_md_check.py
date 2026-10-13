#!/usr/bin/env python3
"""Measure and audit an AGENTS.md file and its harness mirrors.

Reports byte and line counts, the heading map, referenced `just <recipe>`
commands checked against a nearby justfile, referenced repo-relative paths,
and the mirror status of CLAUDE.md, .github/copilot-instructions.md, and
GEMINI.md relative to the canonical AGENTS.md.

Caps: OpenAI Codex concatenates AGENTS.md files from the repository root down
to the working directory. It truncates the file that crosses 32 KiB and drops
every file after it (see references/harness-matrix.md). The script sums every
root-to-directory chain that ends at or below the checked file and applies
the cap to the largest one. A line count over ~200 is a soft readability
flag, not a hard cap.

Root discovery and skip rules match Codex:
- The root is the nearest directory at or above the checked file that
  contains `.git`. With no `.git`, each chain is the checked file only.
- Per directory, `AGENTS.override.md` counts when present, else `AGENTS.md`.
- Sizes are raw on-disk bytes, so CRLF line endings count in full.
- The walk skips dot directories, `node_modules`, broken symlinks, and any
  subdirectory that contains its own `.git` (a nested project root).

Exit 0 when every chain is under the byte cap, no mirror has diverged, and
every referenced recipe and path exists. Exit 1 on a cap breach, on any
drift (diverged mirror, missing recipe, or missing path), or when the file
does not exist. `--json` prints the report dict: path, bytes, chain_bytes,
chain_dir (relative to the root), root_marker, lines, byte_cap, cap_breach,
near_cap, line_warn, headings, justfile, referenced_just_recipes,
missing_recipes, referenced_paths, missing_paths, mirrors, diverged_mirrors,
and drift. `--self-test` runs embedded fixtures instead of scanning a tree.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

BYTE_CAP = 32 * 1024
NEAR_CAP_RATIO = 0.9
LINE_WARN = 200
INSTRUCTION_NAMES = ("AGENTS.override.md", "AGENTS.md")
MIRROR_NAMES = ("CLAUDE.md", ".github/copilot-instructions.md", "GEMINI.md")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
JUST_RECIPE_RE = re.compile(r"^just\s+([A-Za-z_][\w-]*)")
PATH_LIKE_RE = re.compile(r"^[.\w][\w./-]*/[\w./-]*$")
RECIPE_LINE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def _find_justfile(start: Path) -> Path | None:
    for directory in [start, *start.parents]:
        for name in ("justfile", "Justfile"):
            candidate = directory / name
            if candidate.is_file():
                return candidate
    return None


def _repo_root(start: Path) -> Path | None:
    for directory in [start, *start.parents]:
        if (directory / ".git").exists():
            return directory
    return None


def _instruction_bytes(directory: Path) -> int:
    for name in INSTRUCTION_NAMES:
        candidate = directory / name
        if candidate.is_file():
            return candidate.stat().st_size
    return 0


def _largest_chain(agents_path: Path, own_bytes: int) -> tuple[int, str, bool]:
    base = agents_path.parent.resolve()
    base_bytes = _instruction_bytes(base) or own_bytes
    root = _repo_root(base)
    if root is None:
        return base_bytes, ".", False
    prefix = sum(_instruction_bytes(d) for d in base.parents if d.is_relative_to(root))
    totals = {base: prefix + base_bytes}
    best_bytes, best_dir = totals[base], base
    for dirpath, dirnames, filenames in os.walk(base):
        directory = Path(dirpath)
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d != "node_modules" and not (directory / d / ".git").exists()
        ]
        if directory == base:
            continue
        total = totals[directory.parent]
        if any(name in filenames for name in INSTRUCTION_NAMES):
            total += _instruction_bytes(directory)
        totals[directory] = total
        if total > best_bytes:
            best_bytes, best_dir = total, directory
    return best_bytes, best_dir.relative_to(root).as_posix(), True


def _justfile_recipes(justfile: Path) -> set[str]:
    if shutil.which("just"):
        try:
            result = subprocess.run(
                ["just", "--justfile", str(justfile), "--summary"],
                capture_output=True, text=True, timeout=10, check=True,
            )
            names = result.stdout.split()
            if names:
                return set(names)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
    recipes: set[str] = set()
    for line in justfile.read_text(encoding="utf-8").splitlines():
        if not line or line[0] in " \t#[@":
            continue
        if ":" not in line:
            continue
        head, _sep, rest = line.partition(":")
        if rest.startswith("="):
            continue
        tokens = head.split()
        if tokens and RECIPE_LINE_RE.match(tokens[0]):
            recipes.add(tokens[0])
    return recipes


def _headings(text: str) -> list[dict[str, Any]]:
    return [{"level": len(m.group(1)), "text": m.group(2).strip()} for m in HEADING_RE.finditer(text)]


def _referenced_just_recipes(text: str) -> list[str]:
    recipes = []
    for span in BACKTICK_RE.findall(text):
        match = JUST_RECIPE_RE.match(span.strip())
        if match:
            recipes.append(match.group(1))
    return recipes


def _referenced_paths(text: str) -> list[str]:
    paths = []
    for span in BACKTICK_RE.findall(text):
        candidate = span.strip()
        if candidate.startswith(("http://", "https://", "just ")):
            continue
        if PATH_LIKE_RE.match(candidate):
            paths.append(candidate)
    return paths


def _mirror_status(agents_text: str, mirror_path: Path) -> str:
    if not mirror_path.is_file():
        return "absent"
    text = mirror_path.read_text(encoding="utf-8")
    stripped = text.strip()
    if stripped == "@AGENTS.md":
        return "pointer"
    if len(stripped) <= 200 and "AGENTS.md" in stripped and stripped != agents_text.strip():
        return "pointer"
    if text == agents_text:
        return "mirror"
    return "diverged"


def check(agents_path: Path) -> dict[str, Any]:
    text = agents_path.read_text(encoding="utf-8")
    raw_bytes = agents_path.stat().st_size
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    base = agents_path.parent

    justfile = _find_justfile(base)
    known_recipes = _justfile_recipes(justfile) if justfile else set()
    referenced_recipes = _referenced_just_recipes(text)
    missing_recipes = sorted({r for r in referenced_recipes if r not in known_recipes}) if justfile else sorted(set(referenced_recipes))

    referenced_paths = _referenced_paths(text)
    missing_paths = sorted({p for p in referenced_paths if not (base / p).exists()})

    mirrors = {name: _mirror_status(text, base / name) for name in MIRROR_NAMES}
    diverged = sorted(name for name, status in mirrors.items() if status == "diverged")

    chain_bytes, chain_dir, root_marker = _largest_chain(agents_path, raw_bytes)
    cap_breach = chain_bytes > BYTE_CAP
    near_cap = chain_bytes > BYTE_CAP * NEAR_CAP_RATIO
    line_warn = lines > LINE_WARN

    return {
        "path": str(agents_path),
        "bytes": raw_bytes,
        "chain_bytes": chain_bytes,
        "chain_dir": chain_dir,
        "root_marker": root_marker,
        "lines": lines,
        "byte_cap": BYTE_CAP,
        "cap_breach": cap_breach,
        "near_cap": near_cap,
        "line_warn": line_warn,
        "headings": _headings(text),
        "justfile": str(justfile) if justfile else None,
        "referenced_just_recipes": referenced_recipes,
        "missing_recipes": missing_recipes,
        "referenced_paths": referenced_paths,
        "missing_paths": missing_paths,
        "mirrors": mirrors,
        "diverged_mirrors": diverged,
        "drift": bool(diverged) or bool(missing_recipes) or bool(missing_paths),
    }


def _print_report(report: dict[str, Any]) -> None:
    print(f"{report['path']}: {report['bytes']} bytes, {report['lines']} lines")
    if report["chain_bytes"] != report["bytes"]:
        start = "repository root" if report["root_marker"] else "file directory"
        print(f"Combined chain: {report['chain_bytes']} bytes ({start} to {report['chain_dir']})")
    if report["cap_breach"]:
        print(f"FAIL cap breach: {report['chain_bytes']} bytes exceeds the {report['byte_cap']} byte (32 KiB) Codex combined cap")
    elif report["near_cap"]:
        print(f"WARN near cap: {report['chain_bytes']} of {report['byte_cap']} bytes")
    if report["line_warn"]:
        print(f"WARN {report['lines']} lines exceeds the ~200 line soft ceiling")
    print("Headings:")
    for heading in report["headings"]:
        print(f"  {'#' * heading['level']} {heading['text']}")
    if report["justfile"]:
        print(f"Justfile: {report['justfile']}")
    else:
        print("Justfile: not found")
    if report["missing_recipes"]:
        print(f"FAIL missing just recipes: {', '.join(report['missing_recipes'])}")
    if report["missing_paths"]:
        print(f"FAIL missing referenced paths: {', '.join(report['missing_paths'])}")
    print("Mirrors:")
    for name, status in report["mirrors"].items():
        print(f"  {name}: {status}")
    if report["diverged_mirrors"]:
        print(f"FAIL diverged mirrors: {', '.join(report['diverged_mirrors'])}")
    if report["cap_breach"] or report["drift"]:
        print("RESULT: FAIL")
    else:
        print("RESULT: OK")


def _write_fixture(root: Path, name: str, content: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def self_test() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_fixture(root, "justfile", "build:\n\techo build\ntest:\n\techo test\n")
        agents = _write_fixture(
            root, "AGENTS.md",
            "# Agent Instructions\n\nRun `just build` then `just test`.\nSee `README.md`.\n",
        )
        _write_fixture(root, "README.md", "catalog\n")
        report = check(agents)
        if report["cap_breach"] or report["drift"] or report["missing_recipes"] or report["missing_paths"]:
            failures.append(f"clean fixture: expected pass, got {report}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_fixture(root, "justfile", "build:\n\techo build\n")
        agents = _write_fixture(root, "AGENTS.md", "# Agents\n\nRun `just deploy`.\n")
        report = check(agents)
        if "deploy" not in report["missing_recipes"] or not report["drift"]:
            failures.append(f"missing recipe: expected drift, got {report}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        agents = _write_fixture(root, "AGENTS.md", "# Agents\n\nSee `docs/missing.md`.\n")
        report = check(agents)
        if "docs/missing.md" not in report["missing_paths"] or not report["drift"]:
            failures.append(f"missing path: expected drift, got {report}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        agents = _write_fixture(root, "AGENTS.md", "# Agents\n\nShort file.\n")
        _write_fixture(root, "CLAUDE.md", "@AGENTS.md\n")
        report = check(agents)
        if report["mirrors"]["CLAUDE.md"] != "pointer" or report["drift"]:
            failures.append(f"pointer mirror: expected pointer, got {report['mirrors']}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        agents_text = "# Agents\n\nCanonical rules.\n"
        agents = _write_fixture(root, "AGENTS.md", agents_text)
        _write_fixture(root, "GEMINI.md", agents_text)
        report = check(agents)
        if report["mirrors"]["GEMINI.md"] != "mirror" or report["drift"]:
            failures.append(f"identical mirror: expected mirror, got {report['mirrors']}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        agents = _write_fixture(root, "AGENTS.md", "# Agents\n\nCanonical rules.\n")
        _write_fixture(root, ".github/copilot-instructions.md", "# Agents\n\nDifferent rules entirely.\n")
        report = check(agents)
        if report["mirrors"][".github/copilot-instructions.md"] != "diverged" or not report["drift"]:
            failures.append(f"diverged mirror: expected diverged, got {report['mirrors']}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        agents = _write_fixture(root, "AGENTS.md", "# Agents\n\n" + ("x" * (BYTE_CAP + 100)) + "\n")
        report = check(agents)
        if not report["cap_breach"]:
            failures.append("cap breach: expected cap_breach True for oversized file")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        agents = _write_fixture(root, "AGENTS.md", "# Agents\n\n" + "line\n" * (LINE_WARN + 5))
        report = check(agents)
        if not report["line_warn"] or report["cap_breach"]:
            failures.append(f"line warn: expected line_warn True, got {report['lines']} lines")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        half = "# Agents\n\n" + ("x" * (20 * 1024)) + "\n"
        agents = _write_fixture(root, "AGENTS.md", half)
        nested = _write_fixture(root, "pkg/AGENTS.md", half)
        report = check(agents)
        if report["bytes"] > BYTE_CAP or not report["cap_breach"] or report["chain_bytes"] <= BYTE_CAP:
            failures.append(f"combined chain from root: expected cap_breach True, got {report['chain_bytes']} bytes")
        if report["chain_dir"] != "pkg" or not report["root_marker"]:
            failures.append(f"combined chain from root: expected chain_dir pkg, got {report['chain_dir']}")
        report = check(nested)
        if not report["cap_breach"] or report["chain_dir"] != "pkg":
            failures.append(f"combined chain from nested: expected cap_breach True, got {report['chain_bytes']} bytes")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        _write_fixture(root, "AGENTS.md", "r" * 10)
        _write_fixture(root, "a/AGENTS.md", "a" * 20000)
        _write_fixture(root, "b/AGENTS.md", "b" * 25600)
        report = check(root / "AGENTS.md")
        if report["chain_bytes"] != 25610 or report["chain_dir"] != "b" or report["cap_breach"]:
            failures.append(f"sibling subtrees: expected 25610 at b, got {report['chain_bytes']} at {report['chain_dir']}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        agents = root / "AGENTS.md"
        agents.write_bytes(b"line\r\n" * 6000)
        report = check(agents)
        if report["bytes"] != 36000 or not report["cap_breach"]:
            failures.append(f"CRLF raw bytes: expected 36000 and cap_breach, got {report['bytes']}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        half = "x" * (20 * 1024)
        agents = _write_fixture(root, "AGENTS.md", half)
        _write_fixture(root, "ext/lib/AGENTS.md", half)
        (root / "ext/lib/.git").mkdir()
        report = check(agents)
        if report["cap_breach"] or report["chain_bytes"] != report["bytes"]:
            failures.append(f"nested .git boundary: expected no breach, got {report['chain_bytes']} at {report['chain_dir']}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        half = "x" * (20 * 1024)
        agents = _write_fixture(root, "AGENTS.md", half)
        _write_fixture(root, "pkg/AGENTS.md", half)
        report = check(agents)
        if report["cap_breach"] or report["chain_bytes"] != report["bytes"] or report["root_marker"]:
            failures.append(f"no root marker: expected one-file chain, got {report['chain_bytes']} bytes")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        agents = _write_fixture(root, "AGENTS.md", "# Agents\n")
        (root / "pkg").mkdir()
        (root / "pkg/AGENTS.md").symlink_to(root / "missing.md")
        report = check(agents)
        if report["chain_bytes"] != report["bytes"]:
            failures.append(f"broken symlink: expected one-file chain, got {report['chain_bytes']} bytes")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        agents = _write_fixture(root, "AGENTS.md", "# Agents\n")
        _write_fixture(root, "pkg/AGENTS.md", "# Pkg\n")
        _write_fixture(root, "pkg/AGENTS.override.md", "x" * (40 * 1024))
        report = check(agents)
        if not report["cap_breach"] or report["chain_dir"] != "pkg":
            failures.append(f"override file: expected breach at pkg, got {report['chain_bytes']} at {report['chain_dir']}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        agents = _write_fixture(root, "AGENTS.md", "# Agents\n")
        _write_fixture(root, "node_modules/dep/AGENTS.md", "x" * (40 * 1024))
        _write_fixture(root, ".cache/AGENTS.md", "x" * (40 * 1024))
        report = check(agents)
        if report["cap_breach"] or report["chain_dir"] != ".":
            failures.append(f"skip rules: expected no breach at root, got {report['chain_bytes']} at {report['chain_dir']}")

    total = 17
    print(f"self-test: {total - len(failures)}/{total} passed")
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", nargs="?", default="AGENTS.md", help="Path to the AGENTS.md file to check (default: ./AGENTS.md)")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON")
    parser.add_argument("--self-test", action="store_true", help="Run embedded fixtures instead of scanning a real tree")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    agents_path = Path(args.path)
    if not agents_path.is_file():
        print(f"ERROR: {agents_path} not found", file=sys.stderr)
        return 1

    report = check(agents_path)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_report(report)
    return 1 if (report["cap_breach"] or report["drift"]) else 0


if __name__ == "__main__":
    sys.exit(main())
