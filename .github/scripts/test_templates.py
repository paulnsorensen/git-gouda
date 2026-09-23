#!/usr/bin/env python3
"""Regression tests for shipped template assets."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
SETTINGS_PATH = REPO_ROOT / "skills" / "safe-settings" / "assets" / "settings.yml"


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


if __name__ == "__main__":
    unittest.main()
