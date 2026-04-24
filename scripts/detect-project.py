#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
detect-project.py — scan a directory and emit a JSON summary of what kind
of project lives there.

Used by /aiforging:setup as the first step: before asking the user any
questions, we do a read-only scan so we can present findings and make the
interview shorter and smarter.

Output shape (JSON to stdout):

{
  "root": "/absolute/path",
  "name": "folder-name",
  "kind": "backend" | "frontend" | "fullstack" | "meta" | "unknown",
  "backend": {
    "stack":       "symfony-php" | "laravel-php" | "spring-java"
                 | "dotnet-csharp" | "node-ts" | "node-js"
                 | "python" | "ruby-on-rails" | null,
    "orm":         "doctrine" | "eloquent" | "hibernate" | "entity-framework"
                 | "typeorm" | "mikro-orm" | "prisma" | "drizzle" | null,
    "test_runner": "phpunit" | "pest" | "junit" | "dotnet-test" | "vitest"
                 | "jest" | "pytest" | "rspec" | null,
    "evidence":    [ "relative/path/to/file", ... ]
  },
  "frontend": {
    "stack":       "react" | "next" | "vue" | "nuxt" | "svelte"
                 | "angular" | null,
    "language":    "ts" | "js" | null,
    "test_runner": "playwright" | "cypress" | "vitest" | "jest" | null,
    "evidence":    [ "relative/path/to/file", ... ]
  },
  "children": [ { ... same shape, one per sub-repo in a meta-repo ... } ],
  "notes": [ "human-readable observations" ]
}

Contract:
- Never writes. Never modifies files.
- Never follows symlinks outside the root.
- Never reads outside the given root.
- Emits *only* JSON to stdout. Logs go to stderr.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Signal table
# ---------------------------------------------------------------------------
# Each signal is (relative-path, what-it-means). Paths may use simple globs.
# Keep this table small and boring — extend via "stack adapters" later.
# ---------------------------------------------------------------------------

BACKEND_SIGNALS: list[tuple[str, dict[str, str]]] = [
    # Symfony / PHP / Doctrine
    ("symfony.lock",           {"stack": "symfony-php"}),
    ("bin/console",            {"stack": "symfony-php"}),
    ("config/bundles.php",     {"stack": "symfony-php"}),
    # Laravel / PHP / Eloquent
    ("artisan",                {"stack": "laravel-php", "orm": "eloquent"}),
    # composer.json is weak evidence — checked separately
    # Spring / Java
    ("pom.xml",                {"stack": "spring-java"}),
    ("build.gradle",           {"stack": "spring-java"}),
    ("build.gradle.kts",       {"stack": "spring-java"}),
    # .NET / C#
    ("*.sln",                  {"stack": "dotnet-csharp"}),
    ("*.csproj",               {"stack": "dotnet-csharp"}),
    # Node / TS / JS
    ("tsconfig.json",          {"language": "ts"}),
    # package.json checked separately for front vs back
    # Python
    ("pyproject.toml",         {"stack": "python"}),
    ("requirements.txt",       {"stack": "python"}),
    ("manage.py",              {"stack": "python"}),
    # Ruby
    ("Gemfile",                {"stack": "ruby-on-rails"}),
    ("config/application.rb",  {"stack": "ruby-on-rails"}),
]

FRONTEND_SIGNALS: list[tuple[str, dict[str, str]]] = [
    ("next.config.js",         {"stack": "next"}),
    ("next.config.mjs",        {"stack": "next"}),
    ("next.config.ts",         {"stack": "next"}),
    ("nuxt.config.ts",         {"stack": "nuxt"}),
    ("nuxt.config.js",         {"stack": "nuxt"}),
    ("angular.json",           {"stack": "angular"}),
    ("svelte.config.js",       {"stack": "svelte"}),
    ("vite.config.ts",         {"language": "ts"}),
    ("vite.config.js",         {"language": "js"}),
]

TEST_RUNNER_SIGNALS: list[tuple[str, dict[str, str]]] = [
    ("phpunit.xml",            {"test_runner": "phpunit"}),
    ("phpunit.xml.dist",       {"test_runner": "phpunit"}),
    ("pest.xml",               {"test_runner": "pest"}),
    ("playwright.config.ts",   {"test_runner": "playwright"}),
    ("playwright.config.js",   {"test_runner": "playwright"}),
    ("cypress.config.ts",      {"test_runner": "cypress"}),
    ("cypress.config.js",      {"test_runner": "cypress"}),
    ("vitest.config.ts",       {"test_runner": "vitest"}),
    ("vitest.config.js",       {"test_runner": "vitest"}),
    ("jest.config.ts",         {"test_runner": "jest"}),
    ("jest.config.js",         {"test_runner": "jest"}),
    ("pytest.ini",             {"test_runner": "pytest"}),
    ("pyproject.toml:pytest",  {"test_runner": "pytest"}),  # marker
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class BackendInfo:
    stack: str | None = None
    orm: str | None = None
    test_runner: str | None = None
    evidence: list[str] = field(default_factory=list)


@dataclass
class FrontendInfo:
    stack: str | None = None
    language: str | None = None
    test_runner: str | None = None
    evidence: list[str] = field(default_factory=list)


@dataclass
class ProjectInfo:
    root: str
    name: str
    kind: str = "unknown"
    backend: BackendInfo = field(default_factory=BackendInfo)
    frontend: FrontendInfo = field(default_factory=FrontendInfo)
    children: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # When the project is inside a service wrapper (e.g., webapp/application/
    # where webapp/ is the service boundary), this field records the subdirectory
    # name where the actual framework code lives.
    app_subdir: str | None = None

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


# ---------------------------------------------------------------------------
# Scanning helpers
# ---------------------------------------------------------------------------

def _exists_any(root: Path, pattern: str) -> Path | None:
    """True if a file matching pattern exists at the top level of root.

    Supports simple globs (* in filename). Does not recurse.
    """
    if "*" in pattern:
        matches = list(root.glob(pattern))
        return matches[0] if matches else None
    candidate = root / pattern
    return candidate if candidate.exists() else None


def _read_json_safely(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _inspect_package_json(root: Path, info: ProjectInfo) -> None:
    """Classify a package.json as frontend / backend / fullstack."""
    pkg_path = root / "package.json"
    if not pkg_path.exists():
        return
    data = _read_json_safely(pkg_path) or {}
    info.notes.append("package.json present")

    deps: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        if isinstance(data.get(key), dict):
            deps.update(data[key])

    # Frontend signals
    if "react" in deps or "react-dom" in deps:
        info.frontend.stack = info.frontend.stack or "react"
        info.frontend.evidence.append("package.json:react")
    if "next" in deps:
        info.frontend.stack = "next"
        info.frontend.evidence.append("package.json:next")
    if "vue" in deps or "@vue/runtime-core" in deps:
        info.frontend.stack = info.frontend.stack or "vue"
        info.frontend.evidence.append("package.json:vue")
    if "svelte" in deps:
        info.frontend.stack = info.frontend.stack or "svelte"
        info.frontend.evidence.append("package.json:svelte")
    if "@angular/core" in deps:
        info.frontend.stack = "angular"
        info.frontend.evidence.append("package.json:@angular/core")

    # Backend / Node signals
    if "express" in deps or "fastify" in deps or "nestjs" in deps or "@nestjs/core" in deps:
        info.backend.stack = info.backend.stack or ("node-ts" if "typescript" in deps else "node-js")
        info.backend.evidence.append("package.json:node-backend-framework")

    # Node ORMs
    if "typeorm" in deps:
        info.backend.orm = "typeorm"
        info.backend.evidence.append("package.json:typeorm")
    if "@mikro-orm/core" in deps:
        info.backend.orm = "mikro-orm"
        info.backend.evidence.append("package.json:mikro-orm")
    if "prisma" in deps or "@prisma/client" in deps:
        info.backend.orm = "prisma"
        info.backend.evidence.append("package.json:prisma")
    if "drizzle-orm" in deps:
        info.backend.orm = "drizzle"
        info.backend.evidence.append("package.json:drizzle")

    # Node test runners
    if "playwright" in deps or "@playwright/test" in deps:
        info.frontend.test_runner = info.frontend.test_runner or "playwright"
        info.frontend.evidence.append("package.json:playwright")
    if "cypress" in deps:
        info.frontend.test_runner = info.frontend.test_runner or "cypress"
        info.frontend.evidence.append("package.json:cypress")
    if "vitest" in deps:
        if info.frontend.stack:
            info.frontend.test_runner = info.frontend.test_runner or "vitest"
        else:
            info.backend.test_runner = info.backend.test_runner or "vitest"
        info.frontend.evidence.append("package.json:vitest")
    if "jest" in deps:
        if info.frontend.stack:
            info.frontend.test_runner = info.frontend.test_runner or "jest"
        else:
            info.backend.test_runner = info.backend.test_runner or "jest"

    # Language
    if "typescript" in deps or (root / "tsconfig.json").exists():
        info.frontend.language = info.frontend.language or "ts"


def _inspect_composer_json(root: Path, info: ProjectInfo) -> None:
    """Classify a composer.json as Symfony / Laravel / other PHP."""
    composer = root / "composer.json"
    if not composer.exists():
        return
    data = _read_json_safely(composer) or {}
    info.notes.append("composer.json present")
    require = {**data.get("require", {}), **data.get("require-dev", {})}

    if any(k.startswith("symfony/") for k in require):
        info.backend.stack = "symfony-php"
        info.backend.evidence.append("composer.json:symfony/*")
    if any(k.startswith("laravel/") for k in require):
        info.backend.stack = "laravel-php"
        info.backend.evidence.append("composer.json:laravel/*")

    if any("doctrine/orm" in k for k in require):
        info.backend.orm = "doctrine"
        info.backend.evidence.append("composer.json:doctrine/orm")
    if info.backend.stack == "laravel-php":
        info.backend.orm = info.backend.orm or "eloquent"

    if "phpunit/phpunit" in require:
        info.backend.test_runner = info.backend.test_runner or "phpunit"
    if "pestphp/pest" in require:
        info.backend.test_runner = "pest"


def _apply_signal_table(
    root: Path,
    table: list[tuple[str, dict[str, str]]],
    target: BackendInfo | FrontendInfo,
) -> None:
    for pattern, attrs in table:
        # pyproject.toml:pytest is a marker, not a file
        if ":" in pattern:
            continue
        hit = _exists_any(root, pattern)
        if hit is None:
            continue
        rel = str(hit.relative_to(root))
        for key, value in attrs.items():
            if hasattr(target, key) and getattr(target, key) is None:
                setattr(target, key, value)
        target.evidence.append(rel)


def _classify_kind(info: ProjectInfo) -> None:
    has_backend = bool(info.backend.stack)
    has_frontend = bool(info.frontend.stack)
    if has_backend and has_frontend:
        info.kind = "fullstack"
    elif has_backend:
        info.kind = "backend"
    elif has_frontend:
        info.kind = "frontend"
    elif info.children:
        info.kind = "meta"
    else:
        info.kind = "unknown"


def _detect_service_wrapper(
    candidate: Path, manifests: list[str]
) -> Path | None:
    """Check if `candidate` is a service wrapper directory.

    A service wrapper is a directory that has no project manifest of its own
    but contains exactly one subdirectory with a recognized manifest.  Common
    examples:

        webapp/              ← service wrapper (no composer.json here)
        ├── application/     ← actual Symfony app (composer.json here)
        ├── docker/          ← infra, not a project
        └── bin/             ← infra, not a project

    Returns the path to the app subdirectory if a wrapper is detected,
    or None if the directory doesn't match the pattern.
    """
    # Well-known app subdirectory names to check first (ordered by frequency).
    # If none of these exist, fall back to scanning all children.
    well_known = ["application", "app", "src"]
    skip_dirs = {
        "node_modules", "vendor", "dist", "build", "target",
        "bin", "obj", "var", "tmp", "docker", "deploy", "infra",
        "scripts", "docs", "config", ".git",
    }

    # Fast path: check well-known names first
    for name in well_known:
        subdir = candidate / name
        if subdir.is_dir() and any((subdir / m).exists() for m in manifests):
            return subdir

    # Slow path: scan all children for exactly one project-bearing subdir
    project_children: list[Path] = []
    for child in sorted(candidate.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name in skip_dirs:
            continue
        if any((child / m).exists() for m in manifests):
            project_children.append(child)

    # Only treat as a wrapper if there's exactly one project child.
    # Two or more → it's a multi-project dir, not a wrapper.
    if len(project_children) == 1:
        return project_children[0]
    return None


def scan_directory(root: Path, *, recurse_children: bool = True) -> ProjectInfo:
    """Scan one directory. If it looks like a meta-repo (contains sub-repos
    that are themselves projects), scan each sub-repo too."""
    root = root.resolve()
    info = ProjectInfo(root=str(root), name=root.name)

    if not root.exists() or not root.is_dir():
        info.notes.append("directory does not exist or is not a directory")
        return info

    # Top-level signal scan
    _apply_signal_table(root, BACKEND_SIGNALS, info.backend)
    _apply_signal_table(root, FRONTEND_SIGNALS, info.frontend)
    _apply_signal_table(root, TEST_RUNNER_SIGNALS, info.backend)
    _apply_signal_table(root, TEST_RUNNER_SIGNALS, info.frontend)
    _inspect_package_json(root, info)
    _inspect_composer_json(root, info)

    # Meta-repo: check one level down for child projects
    if recurse_children:
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith(".") or child.name in {
                "node_modules", "vendor", "dist", "build",
                "target", "bin", "obj", "var", "tmp",
            }:
                continue
            # Only recurse one level, and only if the child itself looks
            # like a project (has a manifest we recognize).
            manifests = [
                "package.json", "composer.json", "pyproject.toml",
                "pom.xml", "build.gradle", "Gemfile",
            ]
            if any((child / m).exists() for m in manifests):
                child_info = scan_directory(child, recurse_children=False)
                info.children.append(child_info.as_dict())
                continue

            # Service wrapper detection: a directory like webapp/ that
            # doesn't have its own manifest but contains a subdirectory
            # (typically "application/", "app/", or "src/") that does.
            # Common in Dockerized setups where the service dir also holds
            # docker/, bin/, etc. alongside the app code.
            #
            # When detected, we report the wrapper dir as the service root
            # and record which subdirectory holds the actual framework code
            # in the "app_subdir" field, so the setup command can install
            # conventions at the right depth.
            wrapper_child = _detect_service_wrapper(child, manifests)
            if wrapper_child is not None:
                child_info = scan_directory(wrapper_child, recurse_children=False)
                # Re-root the child info to the wrapper directory (the
                # service boundary the user thinks of as "the service").
                child_info.root = str(child.resolve())
                child_info.name = child.name
                child_info.app_subdir = wrapper_child.name
                child_info.notes.append(
                    f"service wrapper detected: framework code lives in "
                    f"{child.name}/{wrapper_child.name}/, service root is "
                    f"{child.name}/"
                )
                info.children.append(child_info.as_dict())

    _classify_kind(info)
    return info


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect the stack and shape of a project directory.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=os.getcwd(),
        help="Directory to scan (default: cwd).",
    )
    parser.add_argument(
        "--no-children",
        action="store_true",
        help="Do not descend into sub-directories looking for child projects.",
    )
    args = parser.parse_args()

    root = Path(args.path).expanduser()
    info = scan_directory(root, recurse_children=not args.no_children)
    json.dump(info.as_dict(), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
