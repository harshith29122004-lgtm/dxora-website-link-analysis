# AI-Powered Website Link Analysis API

A FastAPI application that accepts a public website URL, extracts the page's visible HTML content, and returns structured business and marketing insights using an LLM.

## What it returns

- Brand name, business category and overview.
- Competitor candidates, strengths, gaps and positioning opportunities.
- Five customer search queries covering Google, Facebook, Instagram, LinkedIn and X.
- Primary, secondary and long-tail SEO keywords, a suggested title, meta description and supporting content.
- Five services and a target-audience profile.

The model is instructed to separate observations from suggestions. Competitors are candidates unless independently verified; the API does not invent search volumes, rankings, market share or revenue.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Add your provider key to LLM_API_KEY in .env
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

Open `http://localhost:4000/docs`.

## Request

`POST /link-analysis`

```json
{"url":"https://www.example.com/"}
```

## Project source

The complete source tree, tests, sample response, CI workflow and execution evidence are included in `website-link-analysis-source.tar.xz`. Extract it with `tar -xJf website-link-analysis-source.tar.xz`.

## Verification

- 11 automated tests passed locally.
- Python syntax compilation passed.
- Local Uvicorn startup, health and OpenAPI smoke checks passed.
- Automated provider tests are mocked; a live analysis requires a valid LLM API key.
- The assignment requests a public deployment URL. This repository is not yet deployed to a public host; hosting and configured secrets are required.

See `TEST_RESULTS.md` and `LLM_RESEARCH.md`. Never commit a real `.env` file or API key.
