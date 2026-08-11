#!/usr/bin/env python3
"""Resolve an Anvil menu component value to its expected Vue file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def normalize(value: str) -> str:
    value = value.strip().replace("\\", "/")
    if value.startswith("./"):
        value = value[2:]
    if value.startswith("/"):
        value = value[1:]
    for prefix in ("src/views/", "views/"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
    if value.endswith(".vue"):
        value = value[:-4]
    return value.strip("/")


def expected_path(frontend: Path, component: str) -> Path | None:
    if component in {"Layout", "#", "##"}:
        return None
    if component.startswith("@"):
        alias, sep, rest = component[1:].partition("/")
        if not sep or not rest:
            return frontend / "src" / "platform" / alias
        return frontend / "src" / "platform" / alias / "views" / alias / f"{rest}.vue"
    return frontend / "src" / "views" / f"{component}.vue"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frontend_root", type=Path)
    parser.add_argument("component", help="Menu component value or physical src/views path")
    args = parser.parse_args()

    frontend = args.frontend_root.expanduser().resolve()
    if not (frontend / "package.json").is_file():
        print(f"ERROR: frontend root has no package.json: {frontend}", file=sys.stderr)
        return 2

    normalized = normalize(args.component)
    target = expected_path(frontend, normalized)
    print(f"frontend_root: {frontend}")
    print(f"menu_component: {normalized}")
    if target is None:
        print("physical_file: special layout component")
        return 0

    print(f"physical_file: {target}")
    print(f"exists: {'yes' if target.is_file() else 'no'}")

    router_candidates = [
        frontend / "src" / "utils" / "routerHelper.ts",
        frontend / "src" / "utils" / "routerHelper.js",
    ]
    router = next((path for path in router_candidates if path.is_file()), None)
    if router:
        source = router.read_text(encoding="utf-8", errors="ignore")
        if "viewsModulesImport" in source and "../views/${route.component}.vue" in source:
            print("loader_rule: relative to src/views without .vue")
        else:
            print(f"loader_rule: custom; inspect {router}")
    else:
        print("loader_rule: router helper not found; inspect dynamic route configuration")

    return 0 if target.is_file() else 1


if __name__ == "__main__":
    raise SystemExit(main())
