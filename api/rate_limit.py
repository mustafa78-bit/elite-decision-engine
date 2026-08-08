import ipaddress
from fastapi import Request
from slowapi import Limiter

def is_trusted_proxy(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_loopback or ip.is_private or ip.is_link_local
    except ValueError:
        return False

def get_forwarded_client_ip(request: Request) -> str:
    # Safely get immediate peer IP
    client_host = request.client.host if request.client else "127.0.0.1"

    if not is_trusted_proxy(client_host):
        # Immediate sender is not trusted, do not trust any forwarded headers
        return client_host

    # Check X-Forwarded-For (Traefik appends/sets this)
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # X-Forwarded-For can be a comma-separated list
        ips = [ip.strip() for ip in xff.split(",") if ip.strip()]
        # Traverse right-to-left to find the first untrusted IP
        for ip in reversed(ips):
            if not is_trusted_proxy(ip):
                return ip
        # If all IPs in X-Forwarded-For are trusted proxies, return the leftmost one
        if ips:
            return ips[0]

    # Fall back to X-Real-IP if X-Forwarded-For is not present
    xri = request.headers.get("x-real-ip")
    if xri:
        xri_stripped = xri.strip()
        if not is_trusted_proxy(xri_stripped):
            return xri_stripped

    return client_host

limiter = Limiter(key_func=get_forwarded_client_ip, default_limits=["200/minute"])
