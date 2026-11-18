from fastapi.testclient import TestClient
from app.main import app
from app.services import website_extractor

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_url_is_rejected():
    response = client.post("/link-analysis", json={"url": "not-a-url"})
    assert response.status_code == 422


def test_private_host_is_rejected():
    response = client.post("/link-analysis", json={"url": "http://127.0.0.1/admin"})
    assert response.status_code == 400


def test_non_http_scheme_is_rejected():
    response = client.post("/link-analysis", json={"url": "ftp://example.com/file"})
    assert response.status_code == 422


def test_extractor_cleans_page_content(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {"content-type": "text/html; charset=utf-8"}
        async def aiter_bytes(self):
            yield b'<html><head><title>Acme</title><meta name="description" content="A useful company"></head><body><script>bad()</script><h1>Services</h1><p>We build useful products.</p></body></html>'

    class FakeStream:
        async def __aenter__(self):
            return FakeResponse()
        async def __aexit__(self, *args):
            return False

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        def stream(self, *args, **kwargs): return FakeStream()

    monkeypatch.setattr(website_extractor, "validate_public_url", lambda url: None)
    monkeypatch.setattr(website_extractor.httpx, "AsyncClient", FakeClient)
    import asyncio
    result = asyncio.run(website_extractor.extract_website("https://example.com"))
    assert result["title"] == "Acme"
    assert "Services" in result["headings"]
    assert "bad()" not in result["text"]


def test_link_analysis_returns_all_sections(monkeypatch):
    from app import main
    from app.schemas import Analysis, Brand

    async def fake_extract(url):
        return {
            "url": url,
            "title": "Acme Services",
            "meta_description": "Business services",
            "headings": ["What we do"],
            "text": "Acme provides business services.",
        }

    async def fake_analyse(extracted):
        brand = Brand(name="Acme", category="Business services", summary="A business services company.")
        analysis = Analysis.model_validate({
            "competitor_analysis": {
                "brand_overview": "Acme provides business services.",
                "competitors": [],
                "brand_strengths": ["Clear service focus"],
                "competitive_advantages": ["Specialist approach"],
                "opportunities": ["Publish detailed service pages"],
            },
            "target_search_queries": [
                {"query": f"Acme service query {number}", "platforms": [["Google"], ["Facebook"], ["Instagram"], ["LinkedIn"], ["X"]][number - 1], "intent": "Service research", "business_relevance": "Finds relevant providers", "target_audience": "Small businesses"}
                for number in range(1, 6)
            ],
            "seo_improvements": {
                "primary_keyword": "business services", "secondary_keywords": ["business support"],
                "long_tail_keywords": ["business services for small companies"],
                "recommended_title": "Acme | Business Services", "meta_description": "Business services for growing teams.",
                "supporting_content": ["Service FAQs"],
            },
            "top_services": [
                {"name": f"Service {number}", "description": "A clear service description.", "target_industry": "General", "target_customer": "Small businesses", "main_benefit": "Saves time", "evidence_type": "inferred"}
                for number in range(1, 6)
            ],
            "target_audience": {"primary_audience": ["Small businesses"], "secondary_audience": [], "industries": ["Services"], "business_types": ["SMEs"], "customer_profiles": [], "geographical_focus": [], "customer_needs": ["Reliable support"], "customer_interests": [], "recommended_segments": []},
        })
        return brand, analysis

    monkeypatch.setattr(main, "extract_website", fake_extract)
    monkeypatch.setattr(main, "analyse", fake_analyse)
    response = client.post("/link-analysis", json={"url": "https://example.com"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["brand"]["name"] == "Acme"
    assert len(payload["analysis"]["target_search_queries"]) == 5
    assert len(payload["analysis"]["top_services"]) == 5


def test_redirects_are_not_followed(monkeypatch):
    class FakeResponse:
        status_code = 302
        headers = {"location": "http://127.0.0.1/admin"}

    class FakeStream:
        async def __aenter__(self):
            return FakeResponse()
        async def __aexit__(self, *args):
            return False

    class FakeClient:
        def __init__(self, *args, **kwargs):
            assert kwargs.get("follow_redirects") is False
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False
        def stream(self, *args, **kwargs):
            return FakeStream()

    monkeypatch.setattr(website_extractor, "validate_public_url", lambda url: None)
    monkeypatch.setattr(website_extractor.httpx, "AsyncClient", FakeClient)
    import asyncio
    from fastapi import HTTPException
    import pytest

    with pytest.raises(HTTPException) as error:
        asyncio.run(website_extractor.extract_website("https://example.com"))
    assert error.value.status_code == 400


def test_rejects_non_html_content(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {"content-type": "application/pdf"}

    class FakeStream:
        async def __aenter__(self):
            return FakeResponse()
        async def __aexit__(self, *args):
            return False

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        def stream(self, *args, **kwargs): return FakeStream()

    monkeypatch.setattr(website_extractor, "validate_public_url", lambda url: None)
    monkeypatch.setattr(website_extractor.httpx, "AsyncClient", FakeClient)
    import asyncio
    from fastapi import HTTPException
    import pytest

    with pytest.raises(HTTPException) as error:
        asyncio.run(website_extractor.extract_website("https://example.com/file.pdf"))
    assert error.value.status_code == 415


def test_llm_analysis_requires_provider_key(monkeypatch):
    from app.config import settings
    from app.services.llm_service import analyse
    from fastapi import HTTPException
    import asyncio
    import pytest

    monkeypatch.setattr(settings, "llm_api_key", "")
    with pytest.raises(HTTPException) as error:
        asyncio.run(analyse({"url": "https://example.com", "text": "Example content"}))
    assert error.value.status_code == 503


def test_dns_resolution_with_private_address_is_rejected(monkeypatch):
    import socket
    import pytest
    from fastapi import HTTPException
    from app.services.website_extractor import validate_public_url

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.8", 443)),
        ],
    )
    with pytest.raises(HTTPException) as error:
        validate_public_url("https://mixed.example")
    assert error.value.status_code == 400


def test_llm_response_is_validated_before_returning(monkeypatch):
    import asyncio
    import json
    import sys
    from types import SimpleNamespace
    from app.config import settings
    from app.services.llm_service import analyse

    valid_result = {
        "brand": {"name": "Acme", "category": "Technology", "summary": "A technology business."},
        "competitor_analysis": {
            "brand_overview": "Acme builds software.", "competitors": [],
            "brand_strengths": ["Clear service offer"], "competitive_advantages": [],
            "opportunities": ["Publish case studies"],
        },
        "target_search_queries": [
            {"query": f"Acme software query {index}", "platforms": [["Google"], ["Facebook"], ["Instagram"], ["LinkedIn"], ["X"]][index],
             "intent": "Research", "business_relevance": "Find a provider",
             "target_audience": "Small businesses"}
            for index in range(5)
        ],
        "seo_improvements": {
            "primary_keyword": "Acme software", "secondary_keywords": [],
            "long_tail_keywords": [], "recommended_title": "Acme Software",
            "meta_description": "Software for growing businesses.", "supporting_content": [],
        },
        "top_services": [
            {"name": f"Service {index}", "description": "A service.",
             "target_industry": "Technology", "target_customer": "Businesses",
             "main_benefit": "Saves time", "evidence_type": "inferred"}
            for index in range(5)
        ],
        "target_audience": {"primary_audience": ["Small businesses"]},
    }

    class FakeCompletions:
        async def create(self, **kwargs):
            assert kwargs["response_format"] == {"type": "json_object"}
            assert "untrusted input" in kwargs["messages"][1]["content"]
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(valid_result)))])

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=FakeClient))
    brand, analysis = asyncio.run(analyse({"url": "https://example.com", "text": "Acme builds software."}))
    assert brand.name == "Acme"
    assert len(analysis.target_search_queries) == 5
    assert len(analysis.top_services) == 5
