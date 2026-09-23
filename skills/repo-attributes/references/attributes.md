# Repo attributes references

Sources cited by `SKILL.md`, verified reachable at authoring time.

## `.gitattributes`

- [git-scm.com gitattributes docs](https://git-scm.com/docs/gitattributes) — the canonical attribute reference: `text`, `eol`, `binary`, `merge`, `diff`, `export-ignore`, and the LFS `filter` attribute.

## Linguist overrides

- [github/linguist overrides doc](https://github.com/github/linguist/blob/master/docs/overrides.md) — `linguist-generated`, `linguist-vendored`, `linguist-documentation`, and how each changes the GitHub language bar and default PR diff collapsing.

## `.editorconfig`

- [editorconfig.org](https://editorconfig.org) — the core key reference (`charset`, `end_of_line`, `indent_style`, `indent_size`, `insert_final_newline`, `trim_trailing_whitespace`) and section-matching glob syntax.

## Line endings

- [Configuring Git to handle line endings](https://docs.github.com/en/get-started/getting-started-with-git/configuring-git-to-handle-line-endings) — `core.autocrlf`, `text=auto`, and how `.gitattributes` interacts with per-user Git config.

## `.gitignore`

- [Ignoring files](https://docs.github.com/en/get-started/git-basics/ignoring-files) — `.gitignore` syntax, precedence, and why a tracked file ignores the pattern until `git rm --cached` removes it.

## Git LFS

- [Git LFS](https://git-lfs.com/) — project home, install instructions, and the `filter=lfs diff=lfs merge=lfs -text` attribute pattern.
- [About Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage) — how GitHub stores and bills LFS objects, and `git lfs ls-files` / `git lfs track` usage.
