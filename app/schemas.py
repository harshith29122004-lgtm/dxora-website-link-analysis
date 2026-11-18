from typing import Literal
from pydantic import BaseModel, Field, HttpUrl, model_validator


class AnalysisRequest(BaseModel):
    url: HttpUrl


class Brand(BaseModel):
    name: str
    category: str
    summary: str


class Competitor(BaseModel):
    name: str
    overview: str = "Not established from the available evidence."
    strengths: list[str] = Field(default_factory=list)
    weaknesses_or_gaps: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "low"
    evidence_note: str = "AI-suggested candidate; independently verify before relying on it."


class SearchQuery(BaseModel):
    query: str
    platforms: list[str] = Field(min_length=1)
    intent: str
    business_relevance: str
    target_audience: str


class SEOImprovements(BaseModel):
    primary_keyword: str
    secondary_keywords: list[str] = Field(default_factory=list)
    long_tail_keywords: list[str] = Field(default_factory=list)
    recommended_title: str
    meta_description: str
    supporting_content: list[str] = Field(default_factory=list)


class Service(BaseModel):
    name: str
    description: str
    target_industry: str
    target_customer: str
    main_benefit: str
    evidence_type: Literal["observed", "inferred"] = "observed"


class TargetAudience(BaseModel):
    primary_audience: list[str] = Field(default_factory=list)
    secondary_audience: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    business_types: list[str] = Field(default_factory=list)
    customer_profiles: list[str] = Field(default_factory=list)
    geographical_focus: list[str] = Field(default_factory=list)
    customer_needs: list[str] = Field(default_factory=list)
    customer_interests: list[str] = Field(default_factory=list)
    recommended_segments: list[str] = Field(default_factory=list)


class CompetitorAnalysis(BaseModel):
    brand_overview: str
    competitors: list[Competitor] = Field(default_factory=list)
    brand_strengths: list[str] = Field(default_factory=list)
    competitive_advantages: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)


class Analysis(BaseModel):
    competitor_analysis: CompetitorAnalysis
    target_search_queries: list[SearchQuery] = Field(min_length=5, max_length=5)
    seo_improvements: SEOImprovements
    top_services: list[Service] = Field(min_length=5, max_length=5)
    target_audience: TargetAudience

    @model_validator(mode="after")
    def check_platform_coverage(self):
        required = {"Google", "Facebook", "Instagram", "LinkedIn", "X"}
        included = {
            platform
            for item in self.target_search_queries
            for platform in item.platforms
        }
        missing = required - included
        if missing:
            raise ValueError(
                "Search queries must cover all required platforms; missing: "
                + ", ".join(sorted(missing))
            )
        return self


class SourceInfo(BaseModel):
    page_title: str = ""
    meta_description: str = ""
    headings: list[str] = Field(default_factory=list)
    content_characters: int = 0
    method: str = "HTML extraction + LLM analysis"


class AnalysisResponse(BaseModel):
    success: bool = True
    website: str
    brand: Brand
    analysis: Analysis
    source: SourceInfo
