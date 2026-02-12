import socket
import sys

HOSTNAME = "db.kgxjzpraisfnxeyhyede.supabase.co"

def diagnosis():
    print(f"Diagnosing DNS for: {HOSTNAME}")
    
    # 1. IPv4 (A record)
    try:
        ipv4 = socket.gethostbyname(HOSTNAME)
        print(f"SUCCESS: Resolved to IPv4: {ipv4}")
    except Exception as e:
        print(f"FAILURE: IPv4 Resolution failed: {e}")
        
    # 2. IPv6 (AAAA record)
    try:
        # AF_INET6, SOCK_STREAM
        info = socket.getaddrinfo(HOSTNAME, 5432, socket.AF_INET6, socket.SOCK_STREAM)
        ipv6 = info[0][4][0]
        print(f"SUCCESS: Resolved to IPv6: {ipv6}")
    except Exception as e:
        print(f"FAILURE: IPv6 Resolution failed: {e}")
        
    # 3. All records
    try:
        info = socket.getaddrinfo(HOSTNAME, 5432, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for i in info:
            family = "IPv6" if i[0] == socket.AF_INET6 else "IPv4"
            print(f"Found {family}: {i[4][0]}")
    except Exception as e:
        print(f"FAILURE: General Resolution failed: {e}")

if __name__ == "__main__":
    diagnosis()
