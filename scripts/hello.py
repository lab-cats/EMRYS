#!/usr/bin/env python3

from datetime import datetime
import socket


def main() -> None:
    print(f"Hello from {socket.gethostname()}")
    print(f"Time: {datetime.now()}")


if __name__ == "__main__":
    main()
