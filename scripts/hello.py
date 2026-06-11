# scripts/hello.py
import socket
from datetime import datetime

print("hello from", socket.gethostname())
print("time:", datetime.now())