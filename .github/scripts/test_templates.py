#!/usr/bin/env python3
"""Regression tests for shipped template assets."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
SETTINGS_PATH = REPO_ROOT / "skills" / "safe-settings" / "assets" / "settings.yml"
PR_TITLE_PATH = REPO_ROOT / "skills" / "pr-title-lint" / "assets" / "pr-title.yml"


class SafeSettingsTemplateTest(unittest.TestCase):
    def test_settings_yaml_loads_without_active_labels(self) -> None:
        data = yaml.safe_load(SETTINGS_PATH.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict)
        self.assertNotIn("labels", data)

    def test_labels_exclude_entries_are_named_mappings_if_present(self) -> None:
        data = yaml.safe_load(SETTINGS_PATH.read_text(encoding="utf-8"))
        labels = data.get("labels")
        if labels is None:
            return
        for item in labels.get("exclude", []):
            self.assertIsInstance(item, dict)
            self.assertIsInstance(item.get("name"), str)


class PrTitleTemplateTest(unittest.TestCase):
    def setUp(self) -> None:
        data = yaml.safe_load(PR_TITLE_PATH.read_text(encoding="utf-8"))
        # YAML 1.1 parses the bare `on` key as boolean True.
        self.triggers = data[True]
        self.job = data["jobs"]["pr-title"]

    def test_merge_group_trigger_reports_required_check_in_queue(self) -> None:
        self.assertIn("merge_group", self.triggers)

    def test_title_edits_rerun_the_check(self) -> None:
        self.assertIn("edited", self.triggers["pull_request"]["types"])

    def test_job_runs_only_on_pull_request_events(self) -> None:
        self.assertEqual(self.job.get("if"), "github.event_name == 'pull_request'")

if __name__ == "__main__":
    unittest.main()
