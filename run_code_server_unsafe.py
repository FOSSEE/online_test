#!/usr/bin/env python3
"""
Wrapper script to run code server for local testing without sudo.
This bypasses the security check that requires running as 'nobody' user.

WARNING: Only use this for local testing! Never in production!
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yaksh.code_server import ServerPool, N_CODE_SERVERS, SERVER_POOL_PORT
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description="Run code server for local testing (unsafe mode)")
    parser.add_argument(
        'n', nargs='?', type=int, default=N_CODE_SERVERS,
        help="Number of servers to run."
    )
    parser.add_argument(
        '-p', '--port', dest='port', type=int, default=SERVER_POOL_PORT,
        help="Port at which the http server should run."
    )
    
    options = parser.parse_args()
    
    print(f"🚀 Starting code server on port {options.port} with {options.n} workers")
    print("⚠️  WARNING: Running in UNSAFE mode (no user isolation)")
    print("   Only use for local testing!")
    
    # Create and run server pool WITHOUT calling run_as_nobody()
    server_pool = ServerPool(n=options.n, pool_port=options.port)
    
    try:
        print(f"✅ Code server is running on http://localhost:{options.port}")
        print("   Press Ctrl+C to stop")
        server_pool.run()
    except KeyboardInterrupt:
        print("\n🛑 Stopping code server...")
        server_pool.stop()
        print("✅ Code server stopped")

if __name__ == '__main__':
    main()
