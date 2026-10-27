import os
import sys

# Prevent root mcp.py from shadowing installed 'mcp' package
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
removed_current = False
removed_empty = False

if current_dir in sys.path:
    sys.path.remove(current_dir)
    removed_current = True
if '' in sys.path:
    sys.path.remove('')
    removed_empty = True

# Pre-import real mcp package so sys.modules['mcp'] points to installed library
try:
    import mcp
    import mcp.server
    import mcp.types
except ImportError:
    pass

# Restore sys.path so project modules (e.g., server) remain importable
if removed_current and current_dir not in sys.path:
    sys.path.append(current_dir)
if removed_empty and '' not in sys.path:
    sys.path.append('')
