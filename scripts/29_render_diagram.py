from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def build_command(source: Path, output: Path) -> list[str]:
    suffix = source.suffix.lower()
    if suffix == ".d2":
        binary = shutil.which("d2")
        if not binary:
            raise RuntimeError("renderer d2 introuvable")
        return [binary, str(source), str(output)]
    if suffix in {".puml", ".plantuml"}:
        binary = shutil.which("plantuml")
        if not binary:
            raise RuntimeError("renderer plantuml introuvable")
        return [binary, "-o", str(output.parent), str(source)]
    if suffix == ".dot":
        binary = shutil.which("dot")
        if not binary:
            raise RuntimeError("renderer graphviz/dot introuvable")
        fmt = output.suffix.lower().lstrip(".")
        if fmt not in {"svg", "png"}:
            raise ValueError("Graphviz: sortie attendue .svg ou .png")
        return [binary, f"-T{fmt}", str(source), "-o", str(output)]
    raise ValueError("format source non supporté: utiliser .d2, .puml/.plantuml ou .dot")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rend un diagramme-as-code localement.")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    command = build_command(args.source, args.output)
    if args.dry_run:
        print(" ".join(command))
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
