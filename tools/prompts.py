import os
from tools.core import mcp

@mcp.prompt(name="spotify_rules", description="Rules for interacting with the Spotify MCP server")
def get_spotify_rules() -> str:
    """Return the rules for the Spotify MCP server so Claude Desktop knows how to use it."""
    rules_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SPOTIFY_RULES.md")
    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Always use the registered MCP tools directly for Spotify actions. Do not write python scripts. (Error loading rules: {e})"
