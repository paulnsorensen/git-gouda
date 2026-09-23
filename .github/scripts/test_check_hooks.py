#!/usr/bin/env python3
"""Regression tests for disposable hook checks."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import check_hooks


PRODUCTION_CONFIG = (Path(__file__).resolve().parents[2] / "prek.toml").read_text(encoding="utf-8")


class HookCheckTest(unittest.TestCase):
    def _repo(self, files: dict[str, str]) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "prek.toml").write_text(PRODUCTION_CONFIG, encoding="utf-8")
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "--all"], cwd=root, check=True)
        return temporary, root

    def test_repository_config_runs_all_guard_hooks(self) -> None:
        config = (Path(__file__).resolve().parents[2] / "prek.toml").read_text(encoding="utf-8")
        for hook_id in (
            "trailing-whitespace",
            "end-of-file-fixer",
            "check-yaml",
            "check-json",
            "check-toml",
            "check-merge-conflict",
            "detect-private-key",
            "check-added-large-files",
        ):
            self.assertIn(f'id = "{hook_id}"', config)

    def test_clean_snapshot_passes(self) -> None:
        temporary, root = self._repo({"valid.json": "{}\n", "README.md": "# clean\n"})
        try:
            self.assertEqual(check_hooks.run_checks(root), 0)
        finally:
            temporary.cleanup()

    def test_invalid_json_fails_without_mutation(self) -> None:
        temporary, root = self._repo({"broken.json": "{invalid\n"})
        try:
            before = (root / "broken.json").read_bytes()
            self.assertNotEqual(check_hooks.run_checks(root), 0)
            self.assertEqual((root / "broken.json").read_bytes(), before)
        finally:
            temporary.cleanup()

    def test_private_key_fails_without_mutation(self) -> None:
        private_key = "-----BEGIN " + "PRIVATE KEY-----" + chr(10) + "fixture" + chr(10) + "-----END " + "PRIVATE KEY-----" + chr(10)
        temporary, root = self._repo({"fixture.pem": private_key})
        try:
            before = (root / "fixture.pem").read_bytes()
            self.assertNotEqual(check_hooks.run_checks(root), 0)
            self.assertEqual((root / "fixture.pem").read_bytes(), before)
        finally:
            temporary.cleanup()

    def test_invalid_toml_fails_without_mutation(self) -> None:
        temporary, root = self._repo({"broken.toml": "[broken\n"})
        try:
            before = (root / "broken.toml").read_bytes()
            self.assertNotEqual(check_hooks.run_checks(root), 0)
            self.assertEqual((root / "broken.toml").read_bytes(), before)
        finally:
            temporary.cleanup()

    def test_invalid_yaml_fails_without_mutation(self) -> None:
        temporary, root = self._repo({"broken.yml": "broken: [\n"})
        try:
            before = (root / "broken.yml").read_bytes()
            self.assertNotEqual(check_hooks.run_checks(root), 0)
            self.assertEqual((root / "broken.yml").read_bytes(), before)
        finally:
            temporary.cleanup()

    def test_missing_eof_fails_without_mutation(self) -> None:
        temporary, root = self._repo({"no-eof.txt": "missing final newline"})
        try:
            before = (root / "no-eof.txt").read_bytes()
            self.assertNotEqual(check_hooks.run_checks(root), 0)
            self.assertEqual((root / "no-eof.txt").read_bytes(), before)
        finally:
            temporary.cleanup()

    def test_symlink_is_rejected_without_reading_target(self) -> None:
        temporary, root = self._repo({})
        external_temporary = tempfile.TemporaryDirectory()
        try:
            external = Path(external_temporary.name) / "external.txt"
            external.write_text("outside", encoding="utf-8")
            link = root / "linked.txt"
            link.symlink_to(external)
            self.assertNotEqual(check_hooks.run_checks(root), 0)
            self.assertEqual(external.read_text(encoding="utf-8"), "outside")
        finally:
            external_temporary.cleanup()
            temporary.cleanup()

    def test_merge_conflict_fails_without_mutation(self) -> None:
        conflict = "<<<<<<< HEAD" + chr(10) + "conflict" + chr(10) + "=======" + chr(10) + "other" + chr(10) + ">>>>>>> branch" + chr(10)
        temporary, root = self._repo({"conflict.md": conflict})
        try:
            before = (root / "conflict.md").read_bytes()
            self.assertNotEqual(check_hooks.run_checks(root), 0)
            self.assertEqual((root / "conflict.md").read_bytes(), before)
        finally:
            temporary.cleanup()

    def test_large_file_fails_without_mutation(self) -> None:
        temporary, root = self._repo({"large.txt": "x" * (2 * 1024 * 1024) + chr(10)})
        try:
            before = (root / "large.txt").read_bytes()
            self.assertNotEqual(check_hooks.run_checks(root), 0)
            self.assertEqual((root / "large.txt").read_bytes(), before)
        finally:
            temporary.cleanup()

    def test_fixable_hook_failure_does_not_mutate_caller(self) -> None:
        temporary, root = self._repo({"notes.txt": "trailing spaces  \n"})
        try:
            before = (root / "notes.txt").read_bytes()
            self.assertNotEqual(check_hooks.run_checks(root), 0)
            self.assertEqual((root / "notes.txt").read_bytes(), before)
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
