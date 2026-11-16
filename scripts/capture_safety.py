"""Public network guard for Sauce browser ingestion."""
import ipaddress
import socket
from functools import lru_cache
from urllib.parse import urlsplit

@lru_cache(maxsize=512)
def validate_public_url(url):
    if not isinstance(url,str) or len(url)>2048:
        raise ValueError("Invalid URL")
    p=urlsplit(url)
    if p.scheme not in ("http","https") or not p.hostname:
        raise ValueError("Public HTTP(S) URL required")
    if p.username or p.password or p.fragment or p.query or p.port not in (None,80,443):
        raise ValueError("URL contains forbidden credentials, fragment or port")
    host=p.hostname.lower().strip(".")
    if host=="localhost" or host.endswith((".localhost",".local",".internal",".test")) or "." not in host:
        raise ValueError("Local network host refused")
    try:
        ips=socket.getaddrinfo(host,p.port or (443 if p.scheme=="https" else 80),type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("Public host cannot be resolved") from exc
    if not ips or any(not ipaddress.ip_address(a[4][0]).is_global for a in ips):
        raise ValueError("Nonpublic network address refused")
    return url

def guard_route(route):
    req=route.request
    if req.method not in ("GET","HEAD"):
        return route.abort("blockedbyclient")
    if req.url.startswith(("data:","blob:")):
        return route.continue_()
    try: validate_public_url(req.url)
    except (ValueError,OverflowError): return route.abort("blockedbyclient")
    return route.continue_()
