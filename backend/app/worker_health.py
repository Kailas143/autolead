import threading
import http.server
import socketserver
import os
import subprocess
import sys

PORT = int(os.environ.get("PORT", 8080))

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Worker is healthy")

def run_health_server():
    with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
        print(f"Health check server listening on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Start health check server in a separate thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    # Start the real Celery worker
    print("Starting Celery worker...")
    # This matches your Jenkinsfile args
    cmd = ["celery", "-A", "app.celery_app.celery_app", "worker", "--loglevel=info"]
    subprocess.run(cmd)
