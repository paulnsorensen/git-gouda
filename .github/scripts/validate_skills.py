#!/usr/bin/env python3
"""Validate skill frontmatter, portability, bundled links, and catalog entries."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ALLOWED_KEYS = {
    "name", "description", "license", "compatibility", "metadata",
    "allowed-tools", "version", "argument-hint", "disable-model-invocation",
    "user-invocable", "model", "context", "agent", "hooks",
}
NAME_RE = re.compile(r"^(?!-)(?!.*--)[a-z0-9-]{1,64}(?<!-)$")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\s*(\r?\n|\Z)", re.DOTALL)
DESCRIPTION_MAX_LEN = 1024
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*)$")
CLAUDE_SCOPE_HEADING_RE = re.compile(r"claude[ -]code|claude[ -]only", re.I)
CLAUDE_SCOPE_LINE_RE = re.compile(r"(?im)^\s{0,3}(?:[-*>]\s+)?(?:on\s+)?claude[ -](?:code|only)\b[ ,:-]")
HARNESS_COUPLED_PATTERNS = [
    (re.compile(r"\bAskUserQuestion\b"), "AskUserQuestion (Claude-only tool)"),
    (re.compile(r"\bTodoWrite\b"), "TodoWrite (Claude-only tool)"),
    (re.compile(r"claude\s+mcp\s+add"), "`claude mcp add` (Claude Code CLI)"),
    (re.compile(r"/plugin(?![\w/-])"), "`/plugin` (Claude Code slash command)"),
]
MARKDOWN_LINK_RE = re.compile(r"\]\(([^)]+)\)")
CATALOG_RE = re.compile(r"\|\s*\[([^]]+)\]\(skills/([^/]+)/SKILL\.md\)\s*\|")


def validate_path_shape(path: Path) -> str | None:
    if len(path.parts) != 3 or path.parts[0] != "skills" or path.parts[2] != "SKILL.md":
        return f"{path}: file is not at the documented path skills/<name>/SKILL.md (nested sub-skills are not supported)"
    return None


def validate_frontmatter(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return [f"{path}: missing or malformed YAML frontmatter (expected leading --- ... ---)"]
    try:
        fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return [f"{path}: invalid YAML frontmatter: {exc}"]
    if not isinstance(fm, dict):
        return [f"{path}: frontmatter must be a YAML mapping"]
    errors: list[str] = []
    name, description = fm.get("name"), fm.get("description")
    if "name" not in fm:
        errors.append(f"{path}: missing required key 'name'")
    elif not isinstance(name, str) or not name:
        errors.append(f"{path}: 'name' must be a non-empty string")
    else:
        if not NAME_RE.match(name):
            errors.append(f"{path}: name '{name}' is not kebab-case")
        if name != path.parent.name:
            errors.append(f"{path}: name '{name}' does not match parent directory '{path.parent.name}'")
    if "description" not in fm:
        errors.append(f"{path}: missing required key 'description'")
    elif not isinstance(description, str) or not description.strip():
        errors.append(f"{path}: 'description' must be a non-empty string")
    elif len(description) > DESCRIPTION_MAX_LEN:
        errors.append(f"{path}: 'description' is {len(description)} characters; max is {DESCRIPTION_MAX_LEN} (Codex limit)")
    extra = set(fm) - ALLOWED_KEYS
    if extra:
        errors.append(f"{path}: disallowed frontmatter keys: {sorted(extra)}")
    return errors


def validate_body(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    body = text[match.end():] if match else text
    errors: list[str] = []
    scoped = False
    for line in body.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            scoped = bool(CLAUDE_SCOPE_HEADING_RE.search(heading.group(2)))
            if scoped:
                continue
        if scoped or CLAUDE_SCOPE_LINE_RE.search(line):
            continue
        for pattern, label in HARNESS_COUPLED_PATTERNS:
            if pattern.search(line):
                errors.append(f"{path}: body uses {label} outside a Claude-Code-scoped section — skill bodies must be harness-neutral")
    return errors


def _skill_root(path: Path) -> Path:
    resolved = path.resolve()
    parts = resolved.parts
    try:
        skills_index = max(index for index, part in enumerate(parts) if part == "skills")
    except ValueError:
        return resolved.parent
    if skills_index + 1 >= len(parts):
        return resolved.parent
    return Path(*parts[: skills_index + 2])


def validate_links(path: Path) -> list[str]:
    root = _skill_root(path)
    errors: list[str] = []
    for target in MARKDOWN_LINK_RE.findall(path.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target_path = (path.parent / target.split("#", 1)[0]).resolve()
        if root != target_path and root not in target_path.parents:
            errors.append(f"{path}: bundled resource link escapes skill root: {target}")
        elif not target_path.is_file():
            errors.append(f"{path}: bundled resource link does not exist: {target}")
    return errors
def validate_resource_pointers(path: Path) -> list[str]:
    root = _skill_root(path)
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for pointer in re.findall(r"\x60((?:assets|references|evals)/[^\x60\s]+)\x60", text):
        pointer = pointer.rstrip(".,:;)")
        if pointer.endswith("/"):
            continue
        target_path = (root / pointer).resolve()
        if root != target_path and root not in target_path.parents:
            errors.append(f"{path}: bundled resource pointer escapes skill root: {pointer}")
        elif not target_path.is_file():
            errors.append(f"{path}: bundled resource pointer does not exist: {pointer}")
    return errors
def validate_bundle(skill_file: Path) -> list[str]:
    errors: list[str] = []
    for page in sorted(skill_file.parent.rglob("*.md")):
        if page == skill_file or not ({"references", "evals"} & set(page.parts)):
            continue
        errors.extend(validate_links(page))
        errors.extend(validate_resource_pointers(page))
    return errors




def validate(path: Path) -> list[str]:
    shape_error = validate_path_shape(path)
    if shape_error:
        return [shape_error]
    return validate_frontmatter(path) + validate_body(path) + validate_links(path) + validate_resource_pointers(path)


def validate_catalog(root: Path, skill_files: list[Path]) -> list[str]:
    readme = root / "README.md"
    if not readme.is_file():
        return ["README.md: missing skill catalog (source of truth)"]
    rows = CATALOG_RE.findall(readme.read_text(encoding="utf-8"))
    errors: list[str] = []
    seen: set[str] = set()
    for label, name in rows:
        if name in seen:
            errors.append(f"README.md: duplicate catalog entry for {name!r}")
        seen.add(name)
        if label != name:
            errors.append(f"README.md: catalog label {label!r} does not match skills/{name}/SKILL.md")
    catalog = seen
    actual = {p.parent.name for p in skill_files}
    if catalog != actual:
        errors.append(f"README.md: skill catalog drift (catalog={sorted(catalog)}, files={sorted(actual)})")
    return errors


def main() -> int:
    root = Path(".")
    if not (root / "skills").is_dir():
        print("ERROR: skills/ directory not found", file=sys.stderr)
        return 1
    skill_files = sorted(p for p in root.rglob("SKILL.md") if not any(part.startswith(".") for part in p.parts))
    if not skill_files:
        print("ERROR: no SKILL.md files found in repository", file=sys.stderr)
        return 1
    errors = [error for path in skill_files for error in validate(path)]
    errors.extend(error for path in skill_files for error in validate_bundle(path))
    errors.extend(validate_catalog(root, [p for p in skill_files if validate_path_shape(p) is None]))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"\nFAIL: {len(errors)} error(s) across {len(skill_files)} SKILL.md file(s)", file=sys.stderr)
        return 1
    print(f"OK: validated {len(skill_files)} SKILL.md file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
