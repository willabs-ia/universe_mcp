#!/usr/bin/env python3
"""
Simple HTTP server for Universe MCP frontend.
Serves the web interface on http://localhost:8000
"""

import http.server
import socketserver
import os
import sys

PORT = 8000

# Change to web directory
web_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(web_dir)

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def log_message(self, format, *args):
        # Custom log format
        print(f"[{self.log_date_time_string()}] {format % args}")


if __name__ == '__main__':
    print("=" * 80)
    print("🌌 UNIVERSE MCP - Web Server")
    print("=" * 80)
    print(f"\n📂 Serving from: {web_dir}")
    print(f"🌐 Server running at: http://localhost:{PORT}")
    print(f"\n✨ Open your browser and navigate to: http://localhost:{PORT}")
    print("\n💡 Press Ctrl+C to stop the server\n")
    print("=" * 80)

    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
