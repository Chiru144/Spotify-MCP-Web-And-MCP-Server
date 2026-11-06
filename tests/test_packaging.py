import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_packages = _load("build_packages", ROOT / "packaging" / "build_packages.py")
cli = _load("packaged_cli", ROOT / "packaging" / "spotify-soundtrack-mcp" / "spotify_soundtrack_mcp" / "cli.py")


def test_release_metadata_is_consistent():
    assert build_packages.check() == []


def test_server_json_matches_pypi_package():
    server = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    assert server["name"].startswith("io.github.Chiru144/")
    package = server["packages"][0]
    assert package["registryType"] == "pypi"
    assert package["identifier"] == "spotify-soundtrack-mcp"
    assert package["transport"]["type"] == "stdio"
    assert {"type": "named", "name": "--transport", "value": "stdio"}.items() <= package["packageArguments"][0].items()
    assert len(server["description"]) <= 100


def test_rewrite_imports_targets_installed_package():
    source = (
        "from tools.core import mcp\n"
        "from tools import discovery\n"
        "import tools.search\n"
        '_dispatch("tools.playback", "play")\n'
        "description = 'my tools are great'\n"
    )
    out = build_packages.rewrite_imports(source)
    assert "from spotify_soundtrack_mcp.tools.core import mcp" in out
    assert "from spotify_soundtrack_mcp.tools import discovery" in out
    assert "import spotify_soundtrack_mcp.tools.search" in out
    assert '"spotify_soundtrack_mcp.tools.playback"' in out
    assert "my tools are great" in out


def test_assemble_leaves_no_repo_style_imports(tmp_path):
    mcp_dir, web_dir = build_packages.assemble(tmp_path)
    pkg = mcp_dir / "spotify_soundtrack_mcp"
    assert (pkg / "SPOTIFY_RULES.md").is_file()
    assert len(list((pkg / "skills").glob("*.md"))) == len(list((ROOT / "skills").glob("*.md")))
    assert (web_dir / "spotify_mcp_web" / "templates" / "index.html").is_file()
    for py in list(pkg.rglob("*.py")) + [web_dir / "spotify_mcp_web" / "server.py"]:
        text = py.read_text(encoding="utf-8")
        assert "from tools." not in text and "from tools import" not in text, py
        assert '"tools.' not in text, py


@pytest.mark.parametrize(
    "argv, env, expected",
    [
        ([], {}, "sse"),
        (["--transport", "stdio"], {}, "stdio"),
        (["--transport=STDIO", "--toolsets=core"], {}, "stdio"),
        ([], {"MCP_TRANSPORT": "stdio"}, "stdio"),
        (["--transport", "sse"], {"MCP_TRANSPORT": "stdio"}, "sse"),
    ],
)
def test_cli_transport_selection(argv, env, expected):
    assert cli.get_transport(argv, env) == expected


def test_cli_rejects_unknown_transport():
    with pytest.raises(SystemExit):
        cli.get_transport(["--transport", "websocket"], {})


def test_spotify_skill_prompt_reads_bundled_skill():
    from tools import prompts

    assert "Deduplicator" in prompts.get_spotify_skill("playlist-deduplicator.md")
    assert "not found" in prompts.get_spotify_skill("../../etc/passwd")
