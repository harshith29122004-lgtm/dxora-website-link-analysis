# AI-Powered Website Link Analysis API

This project accepts a public website URL, reads the page's visible HTML content and asks a language model to prepare a structured business review. I kept the first version focused on one page rather than crawling an entire domain, so the analysis has a clear source and the request stays manageable.

## What the API returns

`POST /link-analysis` returns:

- the brand name, business category and a short summary;
- competitor candidates, their possible strengths and gaps, and positioning opportunities;
- five customer search queries mapped to Google, Facebook, Instagram, LinkedIn or X;
- primary, secondary and long-tail SEO keywords, a title, a meta description and supporting content ideas;
- five service entries and a target-audience summary.

Services are labelled `observed` when supported by the submitted page and `inferred` when they are suggestions. Competitor candidates are labelled as suggestions unless the evidence supports stronger confidence. The model is told not to invent search volumes, rankings, market share or other metrics.

The response also includes the extracted page title, description, headings and character count so the caller can see what source material was available to the analysis.

## Technology

- Python 3.10+
- FastAPI, Uvicorn and Pydantic
- HTTPX for asynchronous requests
- BeautifulSoup for HTML extraction
- OpenAI-compatible LLM API (configurable)
- Pytest for automated tests

## Setup

From this project directory:

```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

On macOS or Linux, activate the environment with `source .venv/bin/activate` and copy the example file with `cp .env.example .env`.

Add an API key for the selected provider to `LLM_API_KEY` in `.env`. The default configuration uses OpenAI GPT-6 Luna (`gpt-6-luna`) through the OpenAI API. `LLM_BASE_URL` and `LLM_MODEL` can be changed to use another OpenAI-compatible endpoint. Gemini offers an OpenAI-compatible API surface; check its current documentation before switching. The Anthropic API is not OpenAI-compatible, so it would need a dedicated client adapter before it can be selected directly. Use credentials that belong to your own provider account. Never commit `.env`.

Start the server on the port specified in the practical-test instructions:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

Open `http://localhost:4000/docs` to try the endpoint.

## Request

```http
POST http://localhost:4000/link-analysis
Content-Type: application/json
```

```json
{
  "url": "https://www.example.com/"
}
```

A successful response contains `success`, `website`, `brand`, `analysis` and `source`. The response schema is defined in `app/schemas.py`. See [`examples/sample_response.json`](examples/sample_response.json) for an illustrative response shape. Its business names and recommendations are examples, not results from a live analysis.

## Processing flow

1. Validate the HTTP/HTTPS URL.
2. Resolve the hostname and reject local or non-public addresses.
3. Fetch the HTML page with a timeout and response-size limit.
4. Reject redirects and non-HTML responses.
5. Remove scripts, styles and other non-content elements.
6. Send the cleaned page evidence to the configured LLM.
7. Validate the returned JSON with Pydantic before returning it.

## Error handling and security notes

- Invalid URLs and embedded URL credentials are rejected.
- Localhost, private and non-public IP addresses are rejected.
- Redirects are not followed. If a site redirects, submit its final public URL.
- Non-HTML pages, inaccessible websites, oversized responses, timeouts and empty pages return an HTTP error instead of an invented result.
- Website content is treated as untrusted evidence, not as instructions to the model.
- Provider error details and API keys are not included in the response.

The application checks DNS results before making a request and disables automatic redirects. DNS rebinding is a remaining edge case because the HTTP client performs its own hostname resolution. A production deployment should enforce outbound network rules or use a DNS-pinning transport in addition to this application-level check.

## Tests

```bash
python -m pytest -q
```

The tests cover request validation, private-address rejection (including mixed DNS answers), redirect handling, HTML cleanup, response-size/content handling and LLM response validation. Provider calls are mocked in the automated suite; a live analysis requires a valid API key and network access.

## LLM comparison

See [LLM_RESEARCH.md](LLM_RESEARCH.md). It compares GPT-6 Luna, Gemini 3.8 Flash and Claude Haiku 5.5 using published list prices and a consistent token-budget estimate. Model speed and accuracy have not been benchmarked on a controlled website set; the report explains how to run that comparison.

## Current limitations

- Only the submitted page is analysed; the application does not crawl every page on the domain.
- Competitor names are candidate suggestions, not independently verified market research.
- Search volume, rankings and market-share data are not queried from external SEO tools.
- JavaScript-heavy websites may expose limited content in their initial HTML.
- A real analysis requires a configured LLM API key.

## Project layout

```text
app/
  main.py
  config.py
  schemas.py
  services/
    website_extractor.py
    llm_service.py
tests/
  test_api.py
examples/
  sample_response.json
.github/workflows/tests.yml
.env.example
requirements.txt
LLM_RESEARCH.md
README.md
```

## Deployment note

The application is configured to run locally on port 4000. The employer's brief also asks for a publicly accessible deployment URL and `/docs` link. Those live URLs are not included in this repository because deployment requires a hosting account and a configured LLM API key. Do not present the local address as a public demo. Deploy the app to a host you control, configure the environment variables there, and verify `/health`, `/link-analysis` and `/docs` before sharing a live URL.
