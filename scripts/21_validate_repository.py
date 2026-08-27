from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "README.md",
    "STATUS.md",
    "VERSION",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "pyproject.toml",
    "menu.ps1",
    ".github/powershell/PSScriptAnalyzerSettings.psd1",
    ".github/workflows/ci.yml",
    ".github/workflows/codeql.yml",
    ".github/workflows/dependency-review.yml",
    ".github/workflows/release.yml",
    "config/v1/platform.yaml",
    "config/v1/model_catalog.yaml",
    "config/v1/model_routing.yaml",
    "config/v1/escalation_policy.yaml",
    "config/v1/qualification_policy.yaml",
    "config/v1/role_matrix.yaml",
    "config/v1/security.yaml",
    "config/v1/tool_policy.yaml",
    "config/v1/runtime_versions.json",
    "benchmarks/suites/devops_v1.yaml",
    "docs/ARCHITECTURE.md",
    "docs/INSTALLATION_WINDOWS_11.md",
    "docs/OPENCLAW_INTEGRATION.md",
    "docs/MODELES_LOCAUX.md",
    "docs/ROUTAGE_HYBRIDE.md",
    "docs/BENCHMARK.md",
    "docs/QUALIFICATION.md",
    "docs/OPERATIONS.md",
    "docs/TROUBLESHOOTING.md",
    "docs/GITHUB_GOVERNANCE.md",
    "scripts/benchmark_local.py",
    "scripts/23_evaluate_benchmark.py",
    "scripts/24_validate_release.py",
    "scripts/25_generate_sbom.py",
    "scripts/26_render_openclaw_config.py",
    "scripts/27_route_openclaw.py",
    "scripts/windows/00_bootstrap.ps1",
    "scripts/windows/01_audit_host.ps1",
    "scripts/windows/02_configure_local.ps1",
    "scripts/windows/03_pull_models.ps1",
    "scripts/windows/04_verify_local.ps1",
    "scripts/windows/05_benchmark.ps1",
    "scripts/windows/06_collect_inventory.ps1",
    "scripts/windows/07_run_qualification.ps1",
    "scripts/windows/08_configure_openclaw.ps1",
    "scripts/windows/09_deploy_agents.ps1",
    "scripts/windows/10_test_openclaw_e2e.ps1",
    "scripts/windows/11_install_full.ps1",
    "src/clawlocal/versioning.py",
    "src/clawlocal/openclaw_config.py",
    "src/clawlocal/runtime.py",
    "tests/test_openclaw_config.py",
    "tests/test_runtime.py",
    "tests/test_sbom.py",
    "tests/test_versioning.py",
    "tests/powershell/Repository.Tests.ps1",
}

FORBIDDEN_SUFFIXES = {
    ".gguf",
    ".safetensors",
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".jks",
}
AGENTS = {
    "chef-operations",
    "expert-recherche",
    "architecte-solutions",
    "ingenieur-devops",
    "ingenieur-securite",
    "ingenieur-release-forges",
    "redacteur-technique",
    "auditeur-qualite",
}


def main() -> int:
    failures: list[str] = []

    for relative in sorted(REQUIRED):
        if not (ROOT / relative).is_file():
            failures.append(f"fichier requis absent: {relative}")

    for agent in sorted(AGENTS):
        directory = ROOT / "agents" / agent
        for filename in ("IDENTITY.md", "SOUL.md", "AGENTS.md"):
            if not (directory / filename).is_file():
                failures.append(f"contrat agent absent: agents/{agent}/{filename}")

    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
            failures.append(f"artefact interdit dans Git: {path.relative_to(ROOT)}")

    env_file = ROOT / ".env"
    if env_file.exists():
        failures.append(".env réel présent dans le dépôt")

    if failures:
        for failure in failures:
            print(f"KO  {failure}")
        print(f"\nVerdict: KO ({len(failures)} anomalie(s))")
        return 2

    print(f"OK  structure du dépôt ({len(REQUIRED)} contrats racine/doc/scripts)")
    print(f"OK  équipe IA ({len(AGENTS)} rôles)")
    print("Verdict: CONFORME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
