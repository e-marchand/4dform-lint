from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


def run_cli(*args: str, cwd: Path | None = None, check: bool = True):
    env = {
        "PYTHONPATH": str(PROJECT_DIR / "src"),
    }
    return subprocess.run(
        [sys.executable, "-m", "fourdform_lint", *args],
        cwd=str(cwd or PROJECT_DIR),
        env=env,
        capture_output=True,
        text=True,
        check=check,
    )


class LintCliTests(unittest.TestCase):
    maxDiff = None

    def test_clean_file_passes_without_findings(self):
        result = run_cli(str(FIXTURES_DIR / "basic.form.4DForm"))
        self.assertEqual(result.returncode, 0)
        self.assertIn("No findings", result.stdout)

    def test_overlap_is_reported_as_error(self):
        result = run_cli(str(FIXTURES_DIR / "overlap.form.4DForm"), check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no_overlap", result.stdout)
        self.assertIn("fieldWhenVisible", result.stdout)
        self.assertIn("fieldWhenHidden", result.stdout)

    def test_exclude_can_disable_specific_rules_for_a_run(self):
        result = run_cli(
            str(FIXTURES_DIR / "overlap.form.4DForm"),
            "--exclude",
            "no_overlap,inside_bounds",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("No findings", result.stdout)

    def test_bounds_violation_is_reported(self):
        result = run_cli(str(FIXTURES_DIR / "outside-bounds.form.4DForm"), check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("inside_bounds", result.stdout)

    def test_spacing_warning_does_not_fail_run(self):
        result = run_cli(str(FIXTURES_DIR / "bad-spacing.form.4DForm"))
        self.assertEqual(result.returncode, 0)
        self.assertIn("consistent_spacing", result.stdout)
        self.assertIn("WARNING", result.stdout)

    def test_alignment_warning_is_reported(self):
        result = run_cli(str(FIXTURES_DIR / "bad-alignment.form.4DForm"))
        self.assertEqual(result.returncode, 0)
        self.assertIn("alignment_consistency", result.stdout)
        self.assertIn("left edge is 16 px to the right", result.stdout)

    def test_button_text_overflow_is_reported(self):
        result = run_cli(str(FIXTURES_DIR / "cropped-button.form.4DForm"))
        self.assertEqual(result.returncode, 0)
        self.assertIn("text_fits", result.stdout)
        self.assertIn("saveButton", result.stdout)

    def test_font_size_is_used_when_checking_text_fit(self):
        result = run_cli(str(FIXTURES_DIR / "font-size-text-fit.form.4DForm"))
        self.assertEqual(result.returncode, 0)
        self.assertIn("text_fits", result.stdout)
        self.assertIn("largeTextButton", result.stdout)
        self.assertNotIn("defaultButton", result.stdout)

    def test_horizontal_alignment_warning_reports_top_delta(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            form_path = tmp / "horizontal-alignment.form.4DForm"
            form_path.write_text(
                json.dumps(
                    {
                        "$4d": {"version": "1", "kind": "form"},
                        "destination": "detailScreen",
                        "windowTitle": "Horizontal Alignment",
                        "width": 320,
                        "height": 220,
                        "pages": [
                            {
                                "objects": {
                                    "leftButton": {
                                        "type": "button",
                                        "top": 20,
                                        "left": 20,
                                        "width": 80,
                                        "height": 24,
                                    },
                                    "rightButton": {
                                        "type": "button",
                                        "top": 26,
                                        "left": 112,
                                        "width": 80,
                                        "height": 24,
                                    },
                                }
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = run_cli(str(form_path))
            self.assertEqual(result.returncode, 0)
            self.assertIn("alignment_consistency", result.stdout)
            self.assertIn("top edge is 6 px lower", result.stdout)

    def test_large_spacing_gap_is_not_reported_for_distant_elements(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            form_path = tmp / "distant-spacing.form.4DForm"
            form_path.write_text(
                json.dumps(
                    {
                        "$4d": {"version": "1", "kind": "form"},
                        "destination": "detailScreen",
                        "windowTitle": "Distant Spacing",
                        "width": 640,
                        "height": 800,
                        "pages": [
                            {
                                "objects": {
                                    "leftTitle": {
                                        "type": "text",
                                        "top": 20,
                                        "left": 20,
                                        "width": 120,
                                        "height": 24,
                                    },
                                    "rightButton": {
                                        "type": "button",
                                        "top": 20,
                                        "left": 484,
                                        "width": 120,
                                        "height": 24,
                                    },
                                    "separator": {
                                        "type": "line",
                                        "top": 100,
                                        "left": 20,
                                        "width": 200,
                                        "height": 2,
                                    },
                                    "statusText": {
                                        "type": "text",
                                        "top": 700,
                                        "left": 20,
                                        "width": 200,
                                        "height": 24,
                                    },
                                }
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = run_cli(str(form_path))
            self.assertEqual(result.returncode, 0)
            self.assertIn("No findings", result.stdout)

    def test_wide_list_below_header_row_does_not_trigger_alignment_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            form_path = tmp / "wide-list.form.4DForm"
            form_path.write_text(
                json.dumps(
                    {
                        "$4d": {"version": "1", "kind": "form"},
                        "destination": "detailScreen",
                        "windowTitle": "Wide List",
                        "width": 640,
                        "height": 400,
                        "pages": [
                            {
                                "objects": {
                                    "title": {
                                        "type": "text",
                                        "top": 20,
                                        "left": 16,
                                        "width": 180,
                                        "height": 20,
                                    },
                                    "refresh": {
                                        "type": "button",
                                        "top": 20,
                                        "left": 520,
                                        "width": 100,
                                        "height": 24,
                                    },
                                    "listbox": {
                                        "type": "listbox",
                                        "top": 56,
                                        "left": 16,
                                        "width": 604,
                                        "height": 180,
                                    },
                                }
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = run_cli(str(form_path))
            self.assertEqual(result.returncode, 0)
            self.assertIn("No findings", result.stdout)

    def test_xliff_translation_is_checked_for_text_fit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            form_dir = tmp / "Project" / "Sources" / "Forms" / "LocalizedButton"
            resources_dir = tmp / "Resources" / "fr.lproj"
            form_dir.mkdir(parents=True)
            resources_dir.mkdir(parents=True)
            form_path = form_dir / "form.4DForm"
            xlf_path = resources_dir / "translations.fr.xlf"
            form_path.write_text(
                (FIXTURES_DIR / "localized-button.form.4DForm").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            xlf_path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2">
  <file source-language="en" target-language="fr">
    <body>
      <trans-unit id="cancel_button">
        <source>Cancel</source>
        <target>Annuler la synchronisation</target>
      </trans-unit>
    </body>
  </file>
</xliff>
""",
                encoding="utf-8",
            )
            run_cwd = tmp / "scratch"
            run_cwd.mkdir()
            result = run_cli(str(form_path), cwd=run_cwd)
            self.assertEqual(result.returncode, 0)
            self.assertIn("text_fits", result.stdout)
            self.assertIn("cancel_button", result.stdout)
            self.assertIn("cancelButton", result.stdout)

    def test_xliff_translation_is_not_loaded_outside_project_sources_forms(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            form_dir = tmp / "forms"
            resources_dir = tmp / "Resources" / "fr.lproj"
            form_dir.mkdir(parents=True)
            resources_dir.mkdir(parents=True)
            form_path = form_dir / "localized-button.form.4DForm"
            xlf_path = resources_dir / "translations.fr.xlf"
            form_path.write_text(
                (FIXTURES_DIR / "localized-button.form.4DForm").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            xlf_path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2">
  <file source-language="en" target-language="fr">
    <body>
      <trans-unit id="cancel_button">
        <source>Cancel</source>
        <target>Annuler la synchronisation</target>
      </trans-unit>
    </body>
  </file>
</xliff>
""",
                encoding="utf-8",
            )
            result = run_cli(str(form_path), cwd=tmp)
            self.assertEqual(result.returncode, 0)
            self.assertIn("No findings", result.stdout)
            self.assertNotIn("text_fits", result.stdout)

    def test_invalid_json_is_reported_as_finding(self):
        result = run_cli(str(FIXTURES_DIR / "invalid-json.form.4DForm"), check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid_json", result.stdout)

    def test_schema_validation_is_reported_as_finding(self):
        result = run_cli(str(FIXTURES_DIR / "missing-width.form.4DForm"), check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("schema_validation", result.stdout)

    def test_json_output_contains_summary(self):
        result = run_cli(
            str(FIXTURES_DIR / "overlap.form.4DForm"),
            "--format",
            "json",
            check=False,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["errors"], 1)
        self.assertEqual(payload["files"][0]["findings"][0]["rule_id"], "no_overlap")

    def test_sarif_output_contains_runs(self):
        result = run_cli(
            str(FIXTURES_DIR / "overlap.form.4DForm"),
            "--format",
            "sarif",
            check=False,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["version"], "2.1.0")
        self.assertEqual(payload["runs"][0]["results"][0]["ruleId"], "no_overlap")

    def test_recursive_discovery_uses_deterministic_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            nested = tmp / "forms"
            nested.mkdir()
            (nested / "b.form.4DForm").write_text(
                (FIXTURES_DIR / "overlap.form.4DForm").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (nested / "a.form.4DForm").write_text(
                (FIXTURES_DIR / "basic.form.4DForm").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            result = run_cli(str(nested), "--format", "json", cwd=tmp, check=False)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["files_checked"], 2)
            self.assertEqual(payload["files"][0]["path"], "forms/b.form.4DForm")

    def test_config_can_disable_rule_for_specific_element(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            forms_dir = tmp / "Project" / "Sources" / "Forms" / "Overlap"
            forms_dir.mkdir(parents=True)
            form_path = forms_dir / "form.4DForm"
            form_path.write_text(
                (FIXTURES_DIR / "overlap.form.4DForm").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            config_path = tmp / ".4dform-lint.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "version: 1",
                        "overrides:",
                        "  files:",
                        '    "Project/Sources/Forms/**/*.4DForm":',
                        "      pages:",
                        "        0:",
                        "          elements:",
                        "            fieldWhenHidden:",
                        "              ignore_rules: [no_overlap]",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = run_cli(str(forms_dir), cwd=tmp)
            self.assertEqual(result.returncode, 0)
            self.assertIn("No findings", result.stdout)

    def test_config_can_enable_shared_page_rule_as_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            form_path = tmp / "single.form.4DForm"
            form_path.write_text(
                (FIXTURES_DIR / "basic.form.4DForm").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            config_path = tmp / ".4dform-lint.yaml"
            config_path.write_text(
                "version: 1\nrules:\n  shared_page_required: error\n",
                encoding="utf-8",
            )
            result = run_cli(str(form_path), cwd=tmp, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("shared_page_required", result.stdout)

    def test_invalid_config_exits_with_code_2(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            form_path = tmp / "basic.form.4DForm"
            form_path.write_text(
                (FIXTURES_DIR / "basic.form.4DForm").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (tmp / ".4dform-lint.yaml").write_text(
                "version: 1\nrules:\n  no_overlap: severe\n",
                encoding="utf-8",
            )
            result = run_cli(str(form_path), cwd=tmp, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("must be one of", result.stderr)

    def test_missing_input_path_exits_with_code_2(self):
        result = run_cli("does-not-exist", check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("does not exist", result.stderr)

    def test_unknown_excluded_rule_exits_with_code_2(self):
        result = run_cli(
            str(FIXTURES_DIR / "basic.form.4DForm"),
            "--exclude",
            "not_a_rule",
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown rule id(s) passed to --exclude", result.stderr)


if __name__ == "__main__":
    unittest.main()
