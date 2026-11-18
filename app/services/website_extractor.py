import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException

from app.config import settings

HEADERS = {"User-Agent": "WebsiteLinkAnalysis/1.0 (website content analysis)"}
REDIRECT_CODES = {301, 302, 303, 307, 308}


def validate_public_url(url: str) -> None:
    """Reject malformed URLs and hosts that resolve to non-public IP addresses."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=422, detail="Enter a valid HTTP or HTTPS website URL.")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="URLs containing embedded credentials are not accepted.")
    try:
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="The website URL contains an invalid port.")

    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise HTTPException(status_code=400, detail="Local and internal network addresses cannot be analysed.")

    try:
        # Check literal IP addresses directly; otherwise resolve every returned address.
        try:
            addresses = [ipaddress.ip_address(host)]
        except ValueError:
            records = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
            addresses = [ipaddress.ip_address(record[4][0]) for record in records]
    except (socket.gaierror, ValueError):
        raise HTTPException(status_code=400, detail="The website hostname could not be resolved.")

    if not addresses or any(not address.is_global for address in addresses):
        raise HTTPException(status_code=400, detail="Private or non-public network addresses are not allowed.")


async def extract_website(url: str) -> dict:
    validate_public_url(url)
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    limits = httpx.Limits(max_connections=5, max_keepalive_connections=2)
    try:
        # Redirects are deliberately disabled so a public URL cannot redirect the
        # request into a private network address. The caller can submit the final URL.
        async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=False, headers=HEADERS, trust_env=False) as client:
            async with client.stream("GET", url) as response:
                if response.status_code in REDIRECT_CODES:
                    raise HTTPException(status_code=400, detail="The website redirected. Submit its final URL directly.")
                if response.status_code >= 400:
                    raise HTTPException(status_code=502, detail=f"The website returned HTTP {response.status_code}.")
                if "text/html" not in response.headers.get("content-type", "").lower():
                    raise HTTPException(status_code=415, detail="The submitted URL did not return an HTML page.")
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > settings.max_page_bytes:
                        raise HTTPException(status_code=413, detail="The website page is too large to analyse.")
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="The website took too long to respond.")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch the website ({type(exc).__name__}).")

    soup = BeautifulSoup(bytes(body), "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "template"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description_tag = soup.find("meta", attrs={"name": "description"})
    description = description_tag.get("content", "").strip() if description_tag else ""
    headings = [item.get_text(" ", strip=True) for item in soup.find_all(["h1", "h2", "h3"]) if item.get_text(strip=True)][:35]
    text = " ".join(" ".join(soup.stripped_strings).split())[:settings.max_content_characters]
    if not text and not title and not description:
        raise HTTPException(status_code=422, detail="No readable website content was found.")

    return {"url": url, "title": title, "meta_description": description, "headings": headings, "text": text}
