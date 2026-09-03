from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from clawlocal.project_context import AGENT_IDS
from clawlocal.project_orchestrator_superset import build_phase_prompt

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "v1"
SHARED = ROOT / "agents" / "_shared"

SUPPORTED_LOCAL_MODELS = {
    "qwen-max",
    "gemma-deep",
    "devstral-devops",
}

REQUIRED_PEDAGOGY_MARKERS = (
    "Portée obligatoire",
    "accessible à un débutant",
    "fausse simplification",
    "ton infantilisant",
    "Comprendre",
    "Utiliser",
    "Approfondir",
    "Diagnostiquer",
    "LEARNING_CONTRACT.json",
    "learning_profile.json",
    "documentation_profile.json",
    "preuve pratique",
)

REQUIRED_PHASE_MARKERS = (
    "contrat pédagogique transversal",
    "context/learning/LEARNING_CONTRACT.json",
    "context/learning/learning_profile.json",
    "context/documentation_profile.json",
    "accessible à un débutant",
    "fausse simplification",
    "Comprendre",
    "Utiliser",
    "Approfondir",
    "Diagnostiquer",
)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"racine YAML invalide: {path.relative_to(ROOT)}")
    return value


def _check_true_flags(
    failures: list[str],
    label: str,
    payload: dict[str, Any],
    fields: tuple[str, ...],
) -> None:
    for field in fields:
        if payload.get(field) is not True:
            failures.append(f"{label}: {field} doit être true")


def main() -> int:
    failures: list[str] = []

    pedagogy_path = SHARED / "PEDAGOGY.md"
    if not pedagogy_path.is_file():
        failures.append("contrat pédagogique transversal absent: agents/_shared/PEDAGOGY.md")
        pedagogy_text = ""
    else:
        pedagogy_text = pedagogy_path.read_text(encoding="utf-8")
        for marker in REQUIRED_PEDAGOGY_MARKERS:
            if marker not in pedagogy_text:
                failures.append(f"PEDAGOGY.md: exigence absente: {marker}")

    shared_contract = (SHARED / "CONTRACT.md").read_text(encoding="utf-8")
    for marker in (
        "agents/_shared/PEDAGOGY.md",
        "LEARNING_CONTRACT.json",
        "learning_profile.json",
        "documentation_profile.json",
        "accessible à un débutant",
        "Comprendre, Utiliser, Approfondir et Diagnostiquer",
        "preuve pratique",
    ):
        if marker not in shared_contract:
            failures.append(f"CONTRACT.md: verrou pédagogique absent: {marker}")

    pedagogy = _load_yaml(CONFIG / "pedagogy_policy.yaml")
    pedagogy_enforcement = pedagogy.get("transversal_enforcement", {})
    if not isinstance(pedagogy_enforcement, dict):
        failures.append("pedagogy_policy: transversal_enforcement invalide")
        pedagogy_enforcement = {}
    _check_true_flags(
        failures,
        "pedagogy_policy",
        pedagogy_enforcement,
        (
            "required",
            "applies_to_all_agents",
            "applies_to_all_supported_local_models",
            "applies_to_cloud_escalation_when_used",
            "applies_to_all_orchestrator_phases",
            "beginner_accessible_by_default",
            "preserve_expert_depth",
            "no_role_or_model_bypass",
        ),
    )
    if pedagogy_enforcement.get("shared_prompt_contract") != "agents/_shared/PEDAGOGY.md":
        failures.append("pedagogy_policy: shared_prompt_contract incorrect")
    if pedagogy.get("default_enabled") is not True:
        failures.append("pedagogy_policy: pédagogie désactivée par défaut")
    if pedagogy.get("default_profile") != "balanced":
        failures.append("pedagogy_policy: profil balanced attendu par défaut")
    if pedagogy.get("default_mode") != "assisted":
        failures.append("pedagogy_policy: mode assisted attendu par défaut")

    principles = pedagogy.get("principles", {})
    if not isinstance(principles, dict):
        failures.append("pedagogy_policy: principles invalide")
        principles = {}
    _check_true_flags(
        failures,
        "pedagogy_policy.principles",
        principles,
        (
            "incident_fix_first_debrief_after",
            "never_mark_acquired_from_exposure_only",
            "explain_purpose_before_procedure_when_useful",
            "define_jargon_on_first_use",
            "explain_expected_result_and_validation",
            "explain_risk_limit_and_rollback_when_relevant",
            "no_false_simplification",
            "professional_non_infantilizing_tone",
        ),
    )

    accessibility = _load_yaml(CONFIG / "accessibility_policy.yaml")
    access_enforcement = accessibility.get("transversal_enforcement", {})
    if not isinstance(access_enforcement, dict):
        failures.append("accessibility_policy: transversal_enforcement invalide")
        access_enforcement = {}
    _check_true_flags(
        failures,
        "accessibility_policy",
        access_enforcement,
        (
            "required",
            "applies_to_all_agents",
            "applies_to_all_supported_local_models",
            "applies_to_cloud_escalation_when_used",
            "beginner_accessible_by_default",
            "preserve_expert_depth",
            "no_false_simplification",
        ),
    )

    access_principles = accessibility.get("principles", {})
    if not isinstance(access_principles, dict):
        failures.append("accessibility_policy: principles invalide")
        access_principles = {}
    _check_true_flags(
        failures,
        "accessibility_policy.principles",
        access_principles,
        (
            "technical_accuracy_first",
            "progressive_disclosure",
            "no_false_simplification",
            "no_unstated_critical_prerequisite",
            "define_jargon_on_first_use",
            "preserve_expert_depth",
            "beginner_accessible_without_depth_loss",
            "professional_non_infantilizing_tone",
        ),
    )

    depths = accessibility.get("required_depth_ids", [])
    if depths != ["understand", "operate", "deepen", "diagnose"]:
        failures.append("accessibility_policy: quatre profondeurs progressives requises")

    responsibilities = accessibility.get("role_responsibilities", {})
    if not isinstance(responsibilities, dict) or set(responsibilities) != set(AGENT_IDS):
        failures.append("accessibility_policy: responsabilités pédagogiques requises pour 8 rôles")

    deploy = (ROOT / "scripts" / "windows" / "09_deploy_agents.ps1").read_text(
        encoding="utf-8"
    )
    if "PEDAGOGY.md" not in deploy or "$Pedagogy" not in deploy:
        failures.append("09_deploy_agents.ps1: PEDAGOGY.md doit être chargé")
    merged_marker = '$MergedAgents = @"'
    if merged_marker not in deploy:
        failures.append("09_deploy_agents.ps1: assemblage AGENTS.md introuvable")
    else:
        merged = deploy.split(merged_marker, 1)[1]
        contract_pos = merged.find("$Contract")
        pedagogy_pos = merged.find("$Pedagogy")
        role_pos = merged.find("$RoleAgents")
        if min(contract_pos, pedagogy_pos, role_pos) < 0:
            failures.append("09_deploy_agents.ps1: couches de prompt incomplètes")
        elif not contract_pos < pedagogy_pos < role_pos:
            failures.append(
                "09_deploy_agents.ps1: ordre attendu contrat -> pédagogie -> rôle"
            )

    for agent_id in AGENT_IDS:
        if f"'{agent_id}'" not in deploy:
            failures.append(f"09_deploy_agents.ps1: agent non déployé: {agent_id}")

    intake_source = (ROOT / "src" / "clawlocal" / "project_intake.py").read_text(
        encoding="utf-8"
    )
    if "initialize_learning(destination)" not in intake_source:
        failures.append("project_intake: apprentissage non initialisé à la création")

    context_source = (ROOT / "src" / "clawlocal" / "project_context.py").read_text(
        encoding="utf-8"
    )
    if '_CONTEXT_DIRS = ("intake", "sources", "context")' not in context_source:
        failures.append("project_context: context/ doit être synchronisé vers tous les agents")

    phase_args: dict[str, dict[str, str]] = {
        "analyze": {},
        "plan": {},
        "execute": {"task_id": "task-001"},
        "validate": {},
        "review": {},
    }
    for phase, kwargs in phase_args.items():
        prompt = build_phase_prompt("pedagogy-gate", phase, **kwargs)
        for marker in REQUIRED_PHASE_MARKERS:
            if marker not in prompt:
                failures.append(f"phase {phase}: contexte pédagogique absent: {marker}")
    review_prompt = build_phase_prompt("pedagogy-gate", "review")
    for marker in ("qualité pédagogique", "prérequis explicites", "profondeur expert préservée"):
        if marker not in review_prompt:
            failures.append(f"review: contrôle pédagogique absent: {marker}")

    catalog = _load_yaml(CONFIG / "model_catalog.yaml")
    models = catalog.get("models", {})
    if not isinstance(models, dict) or set(models) != SUPPORTED_LOCAL_MODELS:
        failures.append(
            "model_catalog: flotte locale supportée inattendue pour le gate pédagogique"
        )

    routing = _load_yaml(CONFIG / "model_routing.yaml")
    agents = routing.get("agents", {})
    if not isinstance(agents, dict) or set(agents) != set(AGENT_IDS):
        failures.append("model_routing: les 8 agents doivent être routés")
    else:
        referenced_models: set[str] = set()
        for agent_id, route in agents.items():
            if not isinstance(route, dict):
                failures.append(f"model_routing: route invalide pour {agent_id}")
                continue
            for field, value in route.items():
                if field.startswith("local_") or field == "independent_alternative":
                    if isinstance(value, str):
                        referenced_models.add(value)
                        if value not in SUPPORTED_LOCAL_MODELS:
                            failures.append(
                                f"{agent_id}: modèle local hors flotte dans {field}: {value}"
                            )
        if not SUPPORTED_LOCAL_MODELS.issubset(referenced_models):
            failures.append(
                "model_routing: les trois modèles locaux doivent être effectivement routés"
            )

    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release_text = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    validator_command = "python scripts/46_validate_transversal_pedagogy.py"
    if validator_command not in ci_text:
        failures.append("CI: gate pédagogie transversale absent")
    if validator_command not in release_text:
        failures.append("Release: gate pédagogie transversale absent")

    if failures:
        print("Transversal Pedagogy Gate: NON CONFORME")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Transversal Pedagogy Gate: CONFORME")
    print("- 8 agents: contrat pédagogique obligatoire injecté avant le contrat de rôle")
    print("- 3 modèles locaux: Qwen 3.5 9B, Gemma 3 12B, Qwen 2.5 Coder 14B")
    print("- Ministral 3 14B reste challenger de benchmark hors routage")
    print("- escalade cloud explicite: même contrat pédagogique conservé au niveau agent")
    print("- 5 phases: apprentissage et accessibilité renforcés dans les prompts")
    print("- débutant accessible sans fausse simplification, profondeur expert préservée")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
