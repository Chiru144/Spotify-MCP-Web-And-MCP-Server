import os
import sys
import builtins
import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path

import server
from spotipy.oauth2 import SpotifyPKCE

def gui_input(prompt):
    """Monkey-patch input() so if Spotipy asks for a URL, it shows a popup dialog instead of hanging stdio."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    result = simpledialog.askstring("Spotify Auth Input", prompt)
    root.destroy()
    return result or ""

def check_and_authenticate():
    client_id = os.getenv("SPOTIPY_CLIENT_ID") or os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI") or os.getenv("SPOTIFY_REDIRECT_URI") or "http://127.0.0.1:8888/callback"
    cache_path = str(Path(server.__file__).parent / ".spotipyoauthcache")

    auth_manager = SpotifyPKCE(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=" ".join(server.SPOTIFY_SCOPES),
        cache_path=cache_path,
        open_browser=True,
    )
    
    token_info = auth_manager.validate_token(auth_manager.cache_handler.get_cached_token())
    if not token_info:
        # Patch input so spotipy can't block the MCP stdin if it falls back to manual URL pasting
        builtins.input = gui_input
        
        root = tk.Tk()
        root.title("Spotify MCP Authentication")
        root.geometry("450x250")
        root.eval('tk::PlaceWindow . center')
        root.attributes('-topmost', True)
        
        lbl = tk.Label(root, text="Spotify authentication is required.\nPlease log in to continue using the MCP server.", pady=20, font=("Arial", 12))
        lbl.pack()
        
        def do_login():
            import threading
            import time
            import webbrowser
            import http.server
            import socketserver
            import urllib.parse
            
            btn.config(state=tk.DISABLED, text="Check your browser...")
            root.update()

            def auth_thread():
                try:
                    auth_url = auth_manager.get_authorize_url()
                    webbrowser.open(auth_url)
                    
                    code_received = [None]
                    
                    class TempHandler(http.server.BaseHTTPRequestHandler):
                        def log_message(self, format, *args): pass
                        def do_GET(self):
                            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                            if "code" in qs:
                                code_received[0] = qs["code"][0]
                                self.send_response(200)
                                self.send_header("Content-Type", "text/html")
                                self.end_headers()
                                self.wfile.write(b"<h2>Spotify Authorization Handled!</h2><p>You can close this window.</p>")
                            else:
                                self.send_response(400)
                                self.end_headers()
                                
                    # Try to bind to 8888
                    httpd = None
                    try:
                        class ReusableTCPServer(socketserver.TCPServer):
                            allow_reuse_address = True
                        httpd = ReusableTCPServer(("127.0.0.1", 8888), TempHandler)
                    except Exception:
                        pass # Port in use, server.py will handle it
                        
                    if httpd:
                        # Wait for a single request
                        httpd.timeout = 120
                        httpd.handle_request()
                        httpd.server_close()
                        
                        if code_received[0]:
                            auth_manager.get_access_token(code_received[0])
                            root.after(0, success)
                            return
                            
                    # If we didn't bind, or didn't get a code, poll the cache
                    for _ in range(60):
                        if auth_manager.cache_handler.get_cached_token():
                            root.after(0, success)
                            return
                        time.sleep(1)
                        
                    root.after(0, manual_fallback)
                except Exception as e:
                    root.after(0, lambda: fail(e))

            def success():
                messagebox.showinfo("Success", "Authenticated successfully! Starting MCP server...", parent=root)
                root.destroy()
                
            def fail(e):
                messagebox.showerror("Error", f"Authentication failed: {e}", parent=root)
                root.destroy()
                sys.exit(1)
                
            def manual_fallback():
                url = simpledialog.askstring("Spotify Auth Input", "Please paste the redirect URL here:", parent=root)
                if url:
                    try:
                        code = auth_manager.parse_response_code(url)
                        auth_manager.get_access_token(code)
                        success()
                    except Exception as e:
                        fail(e)
                else:
                    root.destroy()
                    sys.exit(1)

            threading.Thread(target=auth_thread, daemon=True).start()
            
        btn = tk.Button(root, text="Authenticate with Spotify", command=do_login, padx=20, pady=10, bg="#1DB954", fg="white", font=("Arial", 12, "bold"))
        btn.pack()
        
        root.mainloop()

if __name__ == "__main__":
    # 1. First ensure we are authenticated via a GUI popup if necessary
    check_and_authenticate()
    
    # Start the background web app so the UI is available
    auto_open = os.getenv("OPEN_BROWSER", "false").strip().lower() in ("1", "true", "yes")
    server.start_background_web_app(default_port=8000, open_browser=auto_open)
    
    # 2. Read the .md rules and print them to stderr so connecting agents can see them
    rules_path = Path(__file__).parent / "SPOTIFY_RULES.md"
    if rules_path.exists():
        print("\n--- SPOTIFY MCP RULES ---", file=sys.stderr)
        print(rules_path.read_text(encoding="utf-8"), file=sys.stderr)
        print("-------------------------\n", file=sys.stderr)
        
    # Also read any skills if they exist
    for sp in [Path(__file__).parent / "skills", Path(__file__).parent / ".agents" / "skills"]:
        if sp.exists() and sp.is_dir():
            print(f"--- LOADED SKILLS ({sp.name}) ---", file=sys.stderr)
            for skill_file in sorted(sp.glob("*.md")):
                print(f"Skill: {skill_file.name}", file=sys.stderr)
                print(skill_file.read_text(encoding="utf-8"), file=sys.stderr)
            print("---------------------\n", file=sys.stderr)
    
    # 3. Then start the standard MCP Server over stdio
    print(f"Starting Spotify MCP Server via stdio with toolsets: {', '.join(server.active_toolsets)} ({len(server.registered_tools)} tools exposed)...", file=sys.stderr)
    try:
        server.mcp.run()
    except KeyboardInterrupt:
        pass
