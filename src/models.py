from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class WorkingHours(BaseModel):
    day: str
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    is_day_off: bool = False


class Company(BaseModel):
    company_id: int
    url: str
    name: Optional[str] = None
    alt_names: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    website: Optional[str] = None
    telegram: Optional[str] = None
    postal_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    building: Optional[str] = None
    landmarks: list[str] = Field(default_factory=list)
    activity_types: list[str] = Field(default_factory=list)
    rubric_ids: list[int] = Field(default_factory=list)
    inn: Optional[str] = None
    years_on_site: Optional[int] = None
    last_updated: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    working_hours: list[WorkingHours] = Field(default_factory=list)
    source_rubric_id: Optional[int] = None


class SearchParams(BaseModel):
    rubric_ids: list[int] = Field(default_factory=list)
    city_id: Optional[int] = None
    keyword: Optional[str] = None
    output_path: str = "output/result"
    output_format: str = "both"
    delay_min: float = 1.5
    delay_max: float = 3.5
    limit: Optional[int] = None


class ScraperResult(BaseModel):
    total_found: int
    total_exported: int
    duplicates_removed: int
    errors: list[str] = Field(default_factory=list)
    output_files: list[str] = Field(default_factory=list)
