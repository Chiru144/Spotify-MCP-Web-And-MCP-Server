import os
from pathlib import Path

from tools.core import mcp

# Rules and skills sit in the repository root in a source checkout, and inside the
# package directory when installed from PyPI (spotify-soundtrack-mcp).
_HERE = Path(__file__).resolve().parent
_SEARCH_DIRS = [_HERE.parent, _HERE]


def _read_bundled_file(*parts: str) -> str | None:
    """Return the text of a bundled file (e.g. SPOTIFY_RULES.md or skills/<name>.md), or None."""
    for base in _SEARCH_DIRS:
        path = base.joinpath(*parts)
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return None


def _list_skills() -> list[str]:
    names = set()
    for base in _SEARCH_DIRS:
        skills_dir = base / "skills"
        if skills_dir.is_dir():
            names.update(p.stem for p in skills_dir.glob("*.md"))
    return sorted(names)


@mcp.prompt(name="spotify_rules", description="Rules for interacting with the Spotify MCP server")
def get_spotify_rules() -> str:
    """Return the rules for the Spotify MCP server so Claude Desktop knows how to use it."""
    try:
        text = _read_bundled_file("SPOTIFY_RULES.md")
        if text is None:
            raise FileNotFoundError("SPOTIFY_RULES.md")
        return text
    except Exception as e:
        return f"Always use the registered MCP tools directly for Spotify actions. Do not write python scripts. (Error loading rules: {e})"


@mcp.prompt(name="spotify_skill", description="Get instructions from a specific Spotify skill playbook")
def get_spotify_skill(skill_name: str) -> str:
    """Return the markdown instructions for one of the bundled Spotify skill playbooks."""
    clean_name = os.path.basename(skill_name.strip()).removesuffix(".md")
    text = _read_bundled_file("skills", f"{clean_name}.md") if clean_name else None
    if text is not None:
        return text
    available = ", ".join(_list_skills()) or "none"
    return f"Skill '{clean_name}' not found. Available skills: {available}"
