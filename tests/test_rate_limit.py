from fastapi import Request

from api.rate_limit import get_forwarded_client_ip, is_trusted_proxy


def test_is_trusted_proxy():
    # Loopback
    assert is_trusted_proxy("127.0.0.1") is True
    assert is_trusted_proxy("::1") is True

    # Private networks
    assert is_trusted_proxy("10.0.0.1") is True
    assert is_trusted_proxy("172.16.0.1") is True
    assert is_trusted_proxy("172.31.255.255") is True
    assert is_trusted_proxy("192.168.1.100") is True

    # Public IPs (untrusted)
    assert is_trusted_proxy("8.8.8.8") is False
    assert is_trusted_proxy("93.184.216.34") is False
    assert is_trusted_proxy("invalid-ip") is False

def test_untrusted_client_direct_connection():
    # If the immediate peer is not a trusted proxy, X-Forwarded-For must be ignored
    scope = {
        "type": "http",
        "client": ("8.8.8.8", 12345),
        "headers": [
            (b"x-forwarded-for", b"93.184.216.34"),
            (b"x-real-ip", b"93.184.216.34"),
        ],
    }
    request = Request(scope)
    assert get_forwarded_client_ip(request) == "8.8.8.8"

def test_trusted_proxy_single_forwarded_ip():
    # Peer is localhost (trusted proxy), X-Forwarded-For has a public client IP
    scope = {
        "type": "http",
        "client": ("127.0.0.1", 12345),
        "headers": [
            (b"x-forwarded-for", b"93.184.216.34"),
        ],
    }
    request = Request(scope)
    assert get_forwarded_client_ip(request) == "93.184.216.34"

def test_trusted_proxy_multiple_forwarded_ips():
    # Peer is a trusted Docker proxy (e.g. 172.18.0.2).
    # X-Forwarded-For has multiple IPs.
    # The rightmost untrusted IP should be taken.
    scope = {
        "type": "http",
        "client": ("172.18.0.2", 12345),
        "headers": [
            (b"x-forwarded-for", b"93.184.216.34, 172.18.0.3"),
        ],
    }
    request = Request(scope)
    assert get_forwarded_client_ip(request) == "93.184.216.34"

def test_trusted_proxy_all_trusted_forwarded_ips():
    # All IPs in X-Forwarded-For are trusted.
    # It should fall back to the leftmost trusted IP in the chain.
    scope = {
        "type": "http",
        "client": ("172.18.0.2", 12345),
        "headers": [
            (b"x-forwarded-for", b"10.0.0.5, 172.18.0.3"),
        ],
    }
    request = Request(scope)
    assert get_forwarded_client_ip(request) == "10.0.0.5"

def test_trusted_proxy_real_ip_fallback():
    # No X-Forwarded-For, but X-Real-IP is provided and is a public IP.
    scope = {
        "type": "http",
        "client": ("127.0.0.1", 12345),
        "headers": [
            (b"x-real-ip", b"93.184.216.34"),
        ],
    }
    request = Request(scope)
    assert get_forwarded_client_ip(request) == "93.184.216.34"

def test_trusted_proxy_real_ip_fallback_trusted():
    # No X-Forwarded-For, and X-Real-IP is a trusted proxy.
    # It should fallback to request.client.host because X-Real-IP is inside trusted zone.
    scope = {
        "type": "http",
        "client": ("127.0.0.1", 12345),
        "headers": [
            (b"x-real-ip", b"10.0.0.5"),
        ],
    }
    request = Request(scope)
    assert get_forwarded_client_ip(request) == "127.0.0.1"

def test_trusted_proxy_no_headers():
    # No forwarded headers, should fallback to immediate peer
    scope = {
        "type": "http",
        "client": ("127.0.0.1", 12345),
        "headers": [],
    }
    request = Request(scope)
    assert get_forwarded_client_ip(request) == "127.0.0.1"

def test_request_missing_client():
    # Request without client field in scope, should fallback to 127.0.0.1
    scope = {
        "type": "http",
        "headers": [],
    }
    request = Request(scope)
    assert get_forwarded_client_ip(request) == "127.0.0.1"
