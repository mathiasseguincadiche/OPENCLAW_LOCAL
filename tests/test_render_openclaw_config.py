from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_renderer_prefers_checkout_over_stale_pythonpath(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    stale_root = tmp_path / "stale-site-packages"
    stale_package = stale_root / "clawlocal"
    stale_package.mkdir(parents=True)
    (stale_package / "__init__.py").write_text("", encoding="utf-8")
    (stale_package / "openclaw_config.py").write_text(
        "# intentionally stale: SUPPORTED_BACKENDS is absent\n",
        encoding="utf-8",
    )

    output = tmp_path / "openclaw.patch.json"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(stale_root)

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "26_render_openclaw_config.py"),
            "--platform-root",
            str(tmp_path / "platform"),
            "--backend",
            "b580-hybrid",
            "--output",
            str(output),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    patch = json.loads(output.read_text(encoding="utf-8"))
    providers = patch["models"]["providers"]
    assert set(providers) == {"ollama", "intel-vulkan"}
