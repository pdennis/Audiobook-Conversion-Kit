import http.server
import socketserver
import os
import socket
import subprocess
import threading
from pathlib import Path
from podcast_feed import update_feed_after_audiobook

# Update the feed before starting the server
update_feed_after_audiobook(".")

class PodcastHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == "/" or self.path == "/feed" or self.path == "/feed.xml":
                # Serve the RSS feed
                self.send_response(200)
                self.send_header("Content-type", "application/xml")
                self.end_headers()
                
                with open("podcast.xml", "rb") as f:
                    self.wfile.write(f.read())
            elif self.path.startswith("/audio/"):
                # Serve the audio files
                audio_file = self.path.replace("/audio/", "")
                if os.path.exists(audio_file):
                    self.send_response(200)
                    self.send_header("Content-type", "audio/mpeg")
                    self.end_headers()
                    
                    with open(audio_file, "rb") as f:
                        try:
                            self.wfile.write(f.read())
                        except (BrokenPipeError, ConnectionResetError):
                            # Client closed connection
                            return
                else:
                    self.send_error(404, "File not found")
            else:
                # Default handler for other paths
                super().do_GET()
        except (socket.error, ConnectionResetError, BrokenPipeError) as e:
            # Silently handle connection errors
            pass

def start_tailscale_funnel(port):
    """Start a Tailscale funnel to expose the local server to the internet"""
    try:
        # Run tailscale funnel command
        process = subprocess.Popen(
            ["tailscale", "funnel", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Wait for the "Available on the internet:" message
        public_url = None
        for line in process.stdout:
            print(line.strip())
            if "https://" in line and ".ts.net" in line:
                public_url = line.strip()
                break
                
        return process, public_url
    except Exception as e:
        print(f"Failed to start Tailscale funnel: {e}")
        return None, None

def run_server(port=4699, use_tailscale=True):
    """Run the podcast feed server"""
    handler = PodcastHandler
    
    # Allow socket reuse to prevent "Address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True
    
    # Start Tailscale funnel if requested
    funnel_process = None
    if use_tailscale:
        print("Starting Tailscale funnel...")
        funnel_process, public_url = start_tailscale_funnel(port)
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving podcast feed at http://localhost:{port}")
        print(f"- Feed URL: http://localhost:{port}/feed")
        print(f"- Audio files: http://localhost:{port}/audio/FILENAME")
        
        if public_url:
            print(f"\nAvailable on the internet via Tailscale:")
            print(f"- Public feed URL: {public_url.rstrip('/')}/feed")
            print(f"- Public audio files: {public_url.rstrip('/')}/audio/FILENAME")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            if funnel_process:
                funnel_process.terminate()
                print("Tailscale funnel stopped.")

if __name__ == "__main__":
    run_server()