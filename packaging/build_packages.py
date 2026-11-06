"""Build the two PyPI packages from this repository and keep their versions in sync.

The repository runs straight from a checkout (``python server.py``), where the tool
modules are imported as ``tools.*``. On PyPI they ship as:

* ``spotify-soundtrack-mcp``: the MCP server (``tools/``, ``skills/``, ``SPOTIFY_RULES.md``),
  imported as ``spotify_soundtrack_mcp.tools.*``.
* ``spotify-mcp-web``: the Soundtrack Studio (``mcp-soundtrack-app/``).

This script copies the sources next to the files in ``packaging/<package>/``, rewrites
the ``tools`` imports, and runs ``python -m build``.

Usage::

    python packaging/build_packages.py                     # check, assemble and build into dist/
    python packaging/build_packages.py --check             # only check versions and the mcp-name marker
    python packaging/build_packages.py --no-build          # assemble build/packages/ without building
    python packaging/build_packages.py --set-version 1.2.0 # bump both packages and server.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGING = ROOT / "packaging"
SERVER_JSON = ROOT / "server.json"

MCP_PACKAGE = "spotify-soundtrack-mcp"
WEB_PACKAGE = "spotify-mcp-web"
MCP_IMPORT = "spotify_soundtrack_mcp"
WEB_IMPORT = "spotify_mcp_web"

# Package-only files that replace their repository counterparts.
PACKAGE_OVERRIDES = {"__init__.py"}

_VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)
_MCP_NAME_RE = re.compile(r"mcp-name:\s*([A-Za-z0-9.\-]+/[A-Za-z0-9._\-]+)")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+([.\-+][0-9A-Za-z.\-]+)?$")


def rewrite_imports(source: str) -> str:
    """Point ``tools`` imports (and ``"tools.x"`` module strings) at the installed package."""
    source = re.sub(r"\bfrom tools(?=[\s.])", f"from {MCP_IMPORT}.tools", source)
    source = re.sub(r"^(\s*)import tools\b", rf"\1import {MCP_IMPORT}.tools", source, flags=re.MULTILINE)
    source = re.sub(r"""(["'])tools\.(?=\w)""", rf"\1{MCP_IMPORT}.tools.", source)
    return source


def read_version(pyproject: Path) -> str:
    match = _VERSION_RE.search(pyproject.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(f"No version found in {pyproject}")
    return match.group(1)


def check() -> list[str]:
    """Return a list of problems that would make a PyPI or MCP Registry release fail."""
    problems = []
    mcp_version = read_version(PACKAGING / MCP_PACKAGE / "pyproject.toml")
    web_pyproject = (PACKAGING / WEB_PACKAGE / "pyproject.toml").read_text(encoding="utf-8")
    web_version = read_version(PACKAGING / WEB_PACKAGE / "pyproject.toml")
    if mcp_version != web_version:
        problems.append(f"{MCP_PACKAGE} is {mcp_version} but {WEB_PACKAGE} is {web_version}")
    if f'"{MCP_PACKAGE}>={mcp_version}"' not in web_pyproject:
        problems.append(f"{WEB_PACKAGE} should depend on {MCP_PACKAGE}>={mcp_version}")

    server = json.loads(SERVER_JSON.read_text(encoding="utf-8"))
    if server.get("version") != mcp_version:
        problems.append(f"server.json version is {server.get('version')} but {MCP_PACKAGE} is {mcp_version}")
    pypi = [p for p in server.get("packages", []) if p.get("registryType") == "pypi"]
    if not pypi or pypi[0].get("identifier") != MCP_PACKAGE:
        problems.append(f"server.json needs a pypi package with identifier {MCP_PACKAGE}")
    elif pypi[0].get("version") != mcp_version:
        problems.append(f"server.json package version is {pypi[0].get('version')} but {MCP_PACKAGE} is {mcp_version}")
    if len(server.get("description", "")) > 100:
        problems.append("server.json description is longer than 100 characters")

    readme = (PACKAGING / MCP_PACKAGE / "README.md").read_text(encoding="utf-8")
    names = _MCP_NAME_RE.findall(readme)
    if server.get("name") not in names:
        problems.append(
            f"packaging/{MCP_PACKAGE}/README.md must contain 'mcp-name: {server.get('name')}' "
            "(the MCP Registry checks it on PyPI)"
        )
    return problems


def set_version(version: str) -> None:
    if not _SEMVER_RE.match(version):
        raise SystemExit(f"'{version}' is not a version like 1.2.0")
    for name in (MCP_PACKAGE, WEB_PACKAGE):
        path = PACKAGING / name / "pyproject.toml"
        text = _VERSION_RE.sub(f'version = "{version}"', path.read_text(encoding="utf-8"), count=1)
        text = re.sub(rf'"{MCP_PACKAGE}>=[^"]+"', f'"{MCP_PACKAGE}>={version}"', text)
        text = re.sub(rf'"{WEB_PACKAGE}>=[^"]+"', f'"{WEB_PACKAGE}>={version}"', text)
        path.write_text(text, encoding="utf-8")

    server = json.loads(SERVER_JSON.read_text(encoding="utf-8"))
    server["version"] = version
    for package in server.get("packages", []):
        if package.get("identifier") == MCP_PACKAGE:
            package["version"] = version
    SERVER_JSON.write_text(json.dumps(server, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Set {MCP_PACKAGE}, {WEB_PACKAGE} and server.json to {version}")


def _copy_python(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(rewrite_imports(src.read_text(encoding="utf-8")), encoding="utf-8")


def _start_package(name: str, out_dir: Path) -> Path:
    target = out_dir / name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(PACKAGING / name, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for extra in ("LICENSE.md", ".env.sample"):
        shutil.copy2(ROOT / extra, target / extra)
    return target


def assemble(out_dir: Path) -> list[Path]:
    """Lay out both packages under ``out_dir`` and return their directories."""
    out_dir.mkdir(parents=True, exist_ok=True)

    mcp_dir = _start_package(MCP_PACKAGE, out_dir)
    pkg = mcp_dir / MCP_IMPORT
    for src in sorted((ROOT / "tools").glob("*.py")):
        if src.name in PACKAGE_OVERRIDES and (pkg / "tools" / src.name).exists():
            continue
        _copy_python(src, pkg / "tools" / src.name)
    (pkg / "skills").mkdir(exist_ok=True)
    for src in sorted((ROOT / "skills").glob("*.md")):
        shutil.copy2(src, pkg / "skills" / src.name)
    shutil.copy2(ROOT / "SPOTIFY_RULES.md", pkg / "SPOTIFY_RULES.md")

    web_dir = _start_package(WEB_PACKAGE, out_dir)
    web_pkg = web_dir / WEB_IMPORT
    _copy_python(ROOT / "mcp-soundtrack-app" / "server.py", web_pkg / "server.py")
    shutil.copytree(ROOT / "mcp-soundtrack-app" / "templates", web_pkg / "templates", dirs_exist_ok=True)

    return [mcp_dir, web_dir]


def build(package_dirs: list[Path], dist_dir: Path) -> None:
    dist_dir.mkdir(parents=True, exist_ok=True)
    for package_dir in package_dirs:
        print(f"Building {package_dir.name} ...")
        subprocess.run(
            [sys.executable, "-m", "build", "--outdir", str(dist_dir / package_dir.name), str(package_dir)],
            check=True,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="only check that versions and mcp-name are consistent")
    parser.add_argument("--set-version", metavar="X.Y.Z", help="set the version of both packages and server.json")
    parser.add_argument("--no-build", action="store_true", help="assemble the packages without building them")
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "packages", help="where to assemble the packages")
    parser.add_argument("--dist", type=Path, default=ROOT / "dist", help="where to write the wheels and sdists")
    args = parser.parse_args(argv)

    if args.set_version:
        set_version(args.set_version)

    problems = check()
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if problems:
        return 1
    if args.check or args.set_version:
        print("OK: package versions, server.json and the mcp-name marker agree.")
        return 0

    package_dirs = assemble(args.out)
    print("Assembled: " + ", ".join(str(d.relative_to(ROOT)) if d.is_relative_to(ROOT) else str(d) for d in package_dirs))
    if not args.no_build:
        build(package_dirs, args.dist)
        print(f"Wheels and sdists are in {args.dist}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
