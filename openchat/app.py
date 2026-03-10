import argparse
from server import *
import asyncio
from client import *



if __name__ == "__main__":
    # Create the main parser
    parser = argparse.ArgumentParser(
        description="Client-Server Communication Script"
    )
    subparsers = parser.add_subparsers(dest="mode", help="Choose 'server' or 'client' mode")

    # Subparser to start server
    server_start = subparsers.add_parser("server", help="Run as a server")
    server_start.add_argument("--start", action="store_true", help="Start the server")
    server_start.add_argument("--stop", action="store_true", help="Stop the server")
    server_start.add_argument("--host", type=str, default="0.0.0.0", help="Specify the hostname (default 0.0.0.0)")
    server_start.add_argument("-p", "--port", type=int, default=12345, help="Specify the port (default 12345)")
    
     # Subparser for the client mode
    client_start = subparsers.add_parser("client", help="Connect as a client")
    client_start.add_argument("--connect", action="store_true", help="Connect to the server")
    client_start.add_argument("--host", type=str, default="127.0.0.1", help="Specify the server hostname (default 127.0.0.1)")
    client_start.add_argument("-p", "--port", type=int, default=12345, help="Specify the server port (default 12345)")

    # Parse arguments
    args = parser.parse_args()

    # Determine the mode
    if args.mode == "server":
        if args.start:
            try:
                print(f"Starting server at {args.host}:{args.port}...")
                asyncio.run(server(args.host,args.port))
            except Exception as e:
                print(f"Error: {e}")
        elif args.stop:
            pass
    # Add your server logic here
    elif args.mode == "client":
        if args.connect:
            print(f"Connecting to server at {args.host}:{args.port}...")
            asyncio.run(client(args.host,args.port))
    else:
        print("Please specify a mode: server or client")

