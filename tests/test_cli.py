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


if __name__ == "__main__":
    unittest.main()
