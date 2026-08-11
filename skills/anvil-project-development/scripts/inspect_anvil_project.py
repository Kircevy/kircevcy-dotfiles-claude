#!/usr/bin/env python3
"""Read-only structural audit for an unfamiliar Anvil backend/frontend repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable


IGNORED_DIRS = {
    ".git", ".idea", ".vscode", "node_modules", "target", "dist", "build", "coverage"
}


def walk_named(root: Path, filename: str) -> Iterable[Path]:
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        if filename in files:
            yield Path(current) / filename


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(element: ET.Element | None, name: str) -> str | None:
    if element is None:
        return None
    for child in element:
        if local_name(child.tag) == name:
            return (child.text or "").strip() or None
    return None


def descendants(element: ET.Element, name: str) -> list[ET.Element]:
    return [node for node in element.iter() if local_name(node.tag) == name]


def parse_pom(path: Path) -> dict[str, Any] | None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None

    artifact = child_text(root, "artifactId")
    version = child_text(root, "version")
    parent = next((node for node in root if local_name(node.tag) == "parent"), None)
    parent_artifact = child_text(parent, "artifactId")
    parent_version = child_text(parent, "version")
    result: dict[str, Any] = {
        "path": str(path),
        "artifactId": artifact,
        "version": version or parent_version,
        "parentArtifactId": parent_artifact,
    }

    for plugin in descendants(root, "plugin"):
        if child_text(plugin, "artifactId") != "zbiti-generator-maven-plugin":
            continue
        config = next((node for node in plugin if local_name(node.tag) == "configuration"), None)
        config_children = list(config) if config is not None else []
        data_source = next(
            (node for node in config_children if local_name(node.tag) == "dataSource"), None
        )
        password = child_text(data_source, "password")
        literal_secret = bool(password and not re.search(r"\$\{|@.+@", password))
        request_mappings = [
            (node.text or "").strip()
            for node in descendants(config, "requestMapping")
            if (node.text or "").strip()
        ] if config is not None else []
        includes: list[str] = []
        if config is not None:
            for include in descendants(config, "include"):
                includes.extend(
                    (node.text or "").strip()
                    for node in include
                    if local_name(node.tag) == "property" and (node.text or "").strip()
                )
        package_info = next(
            (node for node in config_children if local_name(node.tag) == "packageInfo"), None
        )
        result["generator"] = {
            "pluginVersion": child_text(plugin, "version"),
            "outputDir": child_text(config, "outputDir"),
            "fileOverride": child_text(config, "fileOverride"),
            "generateMdaDomain": child_text(config, "generateMdaDomain"),
            "generateVue": child_text(config, "generateVue"),
            "generateVueVersion": child_text(config, "generateVueVersion"),
            "packageParent": child_text(package_info, "parent"),
            "includeTables": sorted(set(includes)),
            "requestMappings": sorted(set(request_mappings)),
            "literalDatasourceSecret": literal_secret,
        }
        break
    return result


def find_vue_roots(root: Path) -> list[dict[str, Any]]:
    results = []
    for package_path in walk_named(root, "package.json"):
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
        if "vue" not in dependencies:
            continue
        frontend = package_path.parent
        router = next(
            (candidate for candidate in (
                frontend / "src" / "utils" / "routerHelper.ts",
                frontend / "src" / "utils" / "routerHelper.js",
            ) if candidate.is_file()),
            None,
        )
        menu_rule = "unknown"
        platform_aliases = False
        if router:
            source = router.read_text(encoding="utf-8", errors="ignore")
            if "viewsModulesImport" in source and "../views/${route.component}.vue" in source:
                menu_rule = "relative-to-src/views-without-extension"
            platform_aliases = "../platform/${item}/views/${item}/" in source
        results.append({
            "root": str(frontend),
            "name": package.get("name"),
            "version": package.get("version"),
            "vueVersion": dependencies.get("vue"),
            "viewsExists": (frontend / "src" / "views").is_dir(),
            "apiExists": (frontend / "src" / "api").is_dir(),
            "routerHelper": str(router) if router else None,
            "menuComponentRule": menu_rule,
            "platformAliasRouting": platform_aliases,
        })
    return results


def audit(root: Path) -> dict[str, Any]:
    poms = [parsed for path in walk_named(root, "pom.xml") if (parsed := parse_pom(path))]
    anvil_roots = [
        pom for pom in poms
        if "anvil" in " ".join(filter(None, [pom.get("artifactId"), pom.get("parentArtifactId")])).lower()
        or pom.get("generator")
    ]
    modules = [
        pom for pom in poms
        if re.search(r"module-.+-(api|service|rest|rest-spring-boot-starter)$", pom.get("artifactId") or "")
    ]
    return {
        "projectRoot": str(root),
        "anvilPomCandidates": anvil_roots,
        "businessModules": modules,
        "generators": [pom for pom in poms if pom.get("generator")],
        "vueFrontends": find_vue_roots(root),
    }


def print_human(report: dict[str, Any]) -> None:
    print(f"Anvil project audit: {report['projectRoot']}")
    print("\nMaven/Anvil candidates:")
    for pom in report["anvilPomCandidates"]:
        print(f"- {pom['artifactId'] or '?'} {pom['version'] or '?'} :: {pom['path']}")

    print("\nBusiness modules:")
    for module in report["businessModules"]:
        print(f"- {module['artifactId']} :: {module['path']}")

    print("\nGenerators:")
    for pom in report["generators"]:
        cfg = pom["generator"]
        print(f"- POM: {pom['path']}")
        print(f"  plugin: {cfg['pluginVersion'] or '?'}")
        print(f"  output: {cfg['outputDir'] or '?'}")
        print(f"  package: {cfg['packageParent'] or '?'}")
        print(f"  tables: {', '.join(cfg['includeTables']) or '(none detected)'}")
        print(f"  mappings: {', '.join(cfg['requestMappings']) or '(none detected)'}")
        if cfg["literalDatasourceSecret"]:
            print("  WARNING: literal datasource password detected (value redacted)")

    print("\nVue frontends:")
    for frontend in report["vueFrontends"]:
        print(f"- {frontend['name'] or '?'} {frontend['vueVersion'] or '?'} :: {frontend['root']}")
        print(f"  menu component rule: {frontend['menuComponentRule']}")
        print(f"  platform alias routing: {'yes' if frontend['platformAliasRouting'] else 'no'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: project root is not a directory: {root}", file=sys.stderr)
        return 2
    report = audit(root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
