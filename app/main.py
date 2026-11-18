from fastapi import FastAPI
from app.schemas import AnalysisRequest, AnalysisResponse, SourceInfo
from app.services.website_extractor import extract_website
from app.services.llm_service import analyse

app = FastAPI(
    title="AI-Powered Website Link Analysis API",
    version="1.0.0",
    description="Reviews website content and returns structured business, competitor, search, SEO and audience insights.",
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/link-analysis", response_model=AnalysisResponse)
async def link_analysis(request: AnalysisRequest):
    website_url = str(request.url)
    extracted = await extract_website(website_url)
    brand, analysis = await analyse(extracted)
    return AnalysisResponse(
        website=website_url,
        brand=brand,
        analysis=analysis,
        source=SourceInfo(
            page_title=extracted["title"],
            meta_description=extracted["meta_description"],
            headings=extracted["headings"],
            content_characters=len(extracted["text"]),
        ),
    )
