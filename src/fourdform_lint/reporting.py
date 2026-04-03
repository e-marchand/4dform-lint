from __future__ import annotations

import json
from collections import defaultdict

from .models import Finding
from .rules import RULE_SUMMARIES


def summarize(findings: list[Finding], files_checked: int) -> dict[str, int]:
    files_with_findings = len({finding.file_path for finding in findings})
    return {
        "files_checked": files_checked,
        "files_with_findings": files_with_findings,
        "errors": sum(1 for finding in findings if finding.severity == "error"),
        "warnings": sum(1 for finding in findings if finding.severity == "warning"),
    }


def render_text(findings: list[Finding], files_checked: int) -> str:
    summary = summarize(findings, files_checked)
    if not findings:
        return f"Checked {files_checked} file(s). No findings."

    grouped: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        grouped[finding.file_path].append(finding)

    lines: list[str] = []
    for path in sorted(grouped):
        lines.append(path)
        for finding in grouped[path]:
            location = ""
            if finding.page_index is not None:
                location = f"page {finding.page_index}"
                if finding.element_ids:
                    location += f", {', '.join(finding.element_ids)}"
            elif finding.element_ids:
                location = ", ".join(finding.element_ids)
            if location:
                location = f" ({location})"
            lines.append(
                f"  {finding.severity.upper()} {finding.rule_id}{location}: {finding.message}"
            )
    lines.append(
        f"Summary: {summary['files_checked']} checked, {summary['files_with_findings']} with findings, "
        f"{summary['errors']} error(s), {summary['warnings']} warning(s)"
    )
    return "\n".join(lines)


def render_json(findings: list[Finding], files_checked: int) -> str:
    summary = summarize(findings, files_checked)
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for finding in findings:
        grouped[finding.file_path].append(finding.to_dict())

    payload = {
        "summary": summary,
        "files": [
            {"path": path, "findings": grouped[path]}
            for path in sorted(grouped)
        ],
    }
    return json.dumps(payload, indent=2)


def render_sarif(findings: list[Finding], files_checked: int) -> str:
    summary = summarize(findings, files_checked)
    unique_rules = sorted({finding.rule_id for finding in findings})
    rules = [
        {
            "id": rule_id,
            "name": rule_id,
            "shortDescription": {"text": RULE_SUMMARIES.get(rule_id, rule_id)},
        }
        for rule_id in unique_rules
    ]
    results = []
    for finding in findings:
        result = {
            "ruleId": finding.rule_id,
            "level": "warning" if finding.severity == "warning" else "error",
            "message": {"text": finding.message},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": finding.file_path}
                    }
                }
            ],
            "properties": {},
        }
        if finding.page_index is not None:
            result["properties"]["pageIndex"] = finding.page_index
        if finding.element_ids:
            result["properties"]["elementIds"] = list(finding.element_ids)
        results.append(result)

    payload = {
        "version": "2.1.0",
        "$schema": (
            "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json"
        ),
        "runs": [
            {
                "tool": {"driver": {"name": "4dform-lint", "rules": rules}},
                "results": results,
                "properties": {"summary": summary},
            }
        ],
    }
    return json.dumps(payload, indent=2)
