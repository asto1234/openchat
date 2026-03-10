#!/usr/bin/env python3
"""
OpenChat Launcher Script
Provides easy startup for server and client
"""

import subprocess
import sys
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="OpenChat Launcher")
    subparsers = parser.add_subparsers(dest="mode", help="Choose mode")
    
    # Server mode
    server_parser = subparsers.add_parser("server", help="Run as server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Server host")
    server_parser.add_argument("--port", type=int, default=12345, help="Server port")
    
    # Client mode
    client_parser = subparsers.add_parser("client", help="Run as client")
    client_parser.add_argument("--host", default="127.0.0.1", help="Server host")
    client_parser.add_argument("--port", type=int, default=12345, help="Server port")
    
    # Test mode
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--unit", action="store_true", help="Run unit tests")
    test_parser.add_argument("--integration", action="store_true", help="Run integration tests")
    
    args = parser.parse_args()
    
    if args.mode == "server":
        print(f"Starting OpenChat Server on {args.host}:{args.port}...")
        subprocess.run([sys.executable, "secure_server.py", "--host", args.host, "--port", str(args.port)])
    
    elif args.mode == "client":
        print(f"Starting OpenChat Client connecting to {args.host}:{args.port}...")
        subprocess.run([sys.executable, "secure_client.py", "--host", args.host, "--port", str(args.port)])
    
    elif args.mode == "test":
        print("Running tests...")
        if args.unit:
            subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
        else:
            print("Please specify --unit or --integration")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
