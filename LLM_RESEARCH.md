# LLM provider and model comparison

**Reviewed:** 18 November 2026  
**Planning workload:** 5,000 input tokens and 1,500 output tokens per website analysis.

## What matters for this API

The model needs to understand a short extract of website content, separate observations from suggestions, and return a predictable JSON object. For this project, the useful comparison points are API availability, structured-output support, context size, published token price, and the provider's description of response speed. The application has not run a controlled quality or latency benchmark, so this report does not assign made-up accuracy or response-time scores.

## Current model comparison

The prices below are published standard text-token rates in USD per million tokens, checked on 18 November 2026. The estimate uses the same token budget for all three models:

`(5,000 × input price + 1,500 × output price) / 1,000,000`

| Provider | Model / API ID | Input / 1M | Output / 1M | Context window | Estimated cost per analysis | Speed information |
|---|---|---:|---:|---:|---:|---|
| OpenAI | GPT-6 Luna (`gpt-6-luna`) | $0.10 | $0.50 | 1.05M tokens | $0.00125 | Provider positions it as an efficient model for focused, high-volume tasks; no latency number is published here. |
| Google | Gemini 3.8 Flash (`gemini-3.8-flash`) | $0.75* | $3.75* | 1M tokens | $0.009375* | Provider describes it as its most intelligent Flash model; no measured latency for this workload is available. |
| Anthropic | Claude Haiku 5.5 (`claude-haiku-5-5`) | $0.10** | $0.50** | 1M tokens | $0.00125** | Anthropic labels it the fastest Claude model in its current comparison; this is vendor guidance, not a benchmark from this project. |

`*` Gemini 3.8 Flash introductory standard pricing is published through 31 December 2026. The provider's pricing page lists a higher rate beginning 1 January 2027. Check the pricing page again before production use.  
`**` Claude Haiku 5.5's listed rate applies to prompts up to 100,000 input tokens. Prompts above that threshold have higher rates. The sample workload is below the threshold.

These estimates exclude caching, batch discounts, taxes, provider-specific fees, and tokenization differences. Actual usage and invoices depend on the exact prompt and model response.

## Recommendation

For this assignment, GPT-6 Luna is the default recommendation. Its published price is low, its context window is much larger than this one-page workload requires, and the official model page lists structured outputs and the Chat Completions endpoint. That fits the current implementation, which requests JSON and validates it again with Pydantic before returning the result.

Claude Haiku 5.5 is a credible alternative where the provider's latency-sensitive positioning is attractive. Gemini 3.8 Flash is a stronger-capability Flash option, but its current published token price makes it more expensive for the same estimated workload. This is a cost-and-integration recommendation, not a claim that GPT-6 Luna is more accurate. Accuracy must be checked with a representative website evaluation set.

## Accuracy and response speed: what has and has not been measured

No live provider benchmark has been run from this repository. Automated tests mock the provider response so the API's validation and error handling can be tested without consuming API credits. They do not measure model quality or live response time.

A fair evaluation should use the same set of at least 20 websites, equivalent extracted content and prompts, and the same output schema. Record median and 95th-percentile latency, valid-response rate, token usage, actual cost, and reviewer scores for brand identification, competitor relevance, service extraction, SEO usefulness, and audience fit. Reviewers should score anonymised outputs. Also count claims that are not supported by the website.

## Cost controls used in the implementation

- Remove scripts, styles and non-content HTML before sending text to the model.
- Limit the fetched page size and the amount of extracted text.
- Use one model request for all five analysis sections.
- Ask the model to distinguish page evidence from suggestions.
- Validate the JSON with Pydantic before returning it.
- Do not report search volumes, rankings, market share, or revenue without a real data source.
- For a production service, cache completed analyses by normalized URL and content hash with an expiry policy.

## Official references

- OpenAI GPT-6 Luna model details: https://developers.openai.com/api/docs/models/gpt-6-luna
- OpenAI API pricing: https://developers.openai.com/api/docs/pricing
- Google Gemini 3.8 Flash model details: https://ai.google.dev/gemini-api/docs/latest-model
- Google Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- Anthropic Claude Haiku 5.5 model details: https://platform.claude.com/docs/en/models/haiku-5-5/overview
- Anthropic API pricing: https://platform.claude.com/docs/en/about-claude/pricing
