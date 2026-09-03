from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def test_release_workflow_requires_tagged_commit_on_main() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    fetch_main = "git fetch --no-tags origin main:refs/remotes/origin/main"
    ancestry = "git merge-base --is-ancestor HEAD origin/main"
    hardening = "python scripts/47_validate_pre_v1_hardening.py"
    readiness = 'python scripts/24_validate_release.py --tag "${GITHUB_REF_NAME}"'
    build = "python -m build"
    assert fetch_main in text
    assert ancestry in text
    assert text.index(ancestry) < text.index(hardening) < text.index(readiness)
    assert text.index(readiness) < text.index(build)


def test_release_publish_depends_on_python_and_windows_validation() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "needs: [validate-python, validate-windows]" in text
    assert 'gh release create "${GITHUB_REF_NAME}"' in text


def test_release_actions_are_pinned_to_full_commit_sha() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    uses_lines = [line.strip() for line in text.splitlines() if "uses:" in line]
    assert uses_lines
    for line in uses_lines:
        match = re.search(r"uses:\s+[^@\s]+@([0-9a-f]{40})(?:\s|$)", line)
        assert match is not None, f"GitHub Action non pinée sur SHA 40 hex: {line}"
