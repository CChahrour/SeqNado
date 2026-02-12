"""
Unit tests ensuring Snakemake rules include log and message directives.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


RULES_DIR = Path(__file__).parent.parent.parent / "seqnado" / "workflow" / "rules"
SMK_FILES = sorted(RULES_DIR.rglob("*.smk"))
RULE_RE = re.compile(r"^\s*rule\s+([A-Za-z0-9_]+)\s*:")


def _iter_rule_sections(content: str):
    """Yield (rule_name, section_text) pairs for a smk file."""
    lines = content.splitlines()
    rule_starts = []

    for index, line in enumerate(lines):
        match = RULE_RE.match(line)
        if match:
            rule_starts.append((match.group(1), index))

    for start_index, (rule_name, rule_line_index) in enumerate(rule_starts):
        section_lines = []
        scan_index = rule_line_index + 1
        while scan_index < len(lines):
            line = lines[scan_index]
            if RULE_RE.match(line) or line.startswith("ruleorder:"):
                break
            section_lines.append(line)
            scan_index += 1
        yield rule_name, "\n".join(section_lines)


@pytest.mark.unit
@pytest.mark.parametrize("smk_file", SMK_FILES)
def test_rule_sections_have_benchmark_log_and_message(smk_file: Path):
    """Test that each rule section declares log and message directives."""
    content = smk_file.read_text()
    sections = list(_iter_rule_sections(content))

    if not sections:
        pytest.skip(f"No rule declarations found in {smk_file}")

    for rule_name, section in sections:
        assert "benchmark:" in section, f"{smk_file} rule {rule_name} missing benchmark:"
        assert "log:" in section, f"{smk_file} rule {rule_name} missing log:"
        assert "message:" in section, f"{smk_file} rule {rule_name} missing message:"
