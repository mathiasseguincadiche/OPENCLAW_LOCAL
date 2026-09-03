from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import benchmark_qualification_40m as hard40  # noqa: E402
import benchmark_qualification_40m_v2 as hard40_v2  # noqa: E402


def test_v2_restores_qwen_native_output_headroom_without_import_side_effect() -> None:
    assert hard40.QWEN_NATIVE_MAX_OUTPUT_TOKENS == 640
    assert hard40_v2.QWEN_NATIVE_MAX_OUTPUT_TOKENS == 768
