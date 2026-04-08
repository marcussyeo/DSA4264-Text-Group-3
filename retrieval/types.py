from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SearchMode = Literal["find_jobs", "find_modules"]


@dataclass(slots=True)
class MatchedEntity:
    type: str
    value: str
    label: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class JobRecommendation:
    jobId: str
    title: str
    company: str
    categories: list[str]
    score: float
    reason: str
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ModuleRecommendation:
    moduleCode: str
    title: str
    department: str
    score: float
    reason: str
    descriptionSnippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SearchResponse:
    mode: SearchMode
    normalizedQuery: str
    matchedEntity: MatchedEntity | None = None
    warnings: list[str] = field(default_factory=list)
    results: list[JobRecommendation | ModuleRecommendation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "normalizedQuery": self.normalizedQuery,
            "matchedEntity": None if self.matchedEntity is None else self.matchedEntity.to_dict(),
            "warnings": list(self.warnings),
            "results": [result.to_dict() for result in self.results],
        }
