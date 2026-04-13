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
    descriptionSnippet: str = ""
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ModuleRecommendation:
    moduleCode: str
    title: str
    context: str
    score: float
    reason: str
    descriptionSnippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DegreeRecommendation:
    degreeId: str
    degreeLabel: str
    reason: str
    moduleCount: int = 0
    score: float | None = None

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


@dataclass(slots=True)
class ExplorerResponse:
    intent: str
    normalizedQuery: str
    matchedEntity: MatchedEntity | None = None
    warnings: list[str] = field(default_factory=list)
    jobs: list[JobRecommendation] = field(default_factory=list)
    modules: list[ModuleRecommendation] = field(default_factory=list)
    degrees: list[DegreeRecommendation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "normalizedQuery": self.normalizedQuery,
            "matchedEntity": None if self.matchedEntity is None else self.matchedEntity.to_dict(),
            "warnings": list(self.warnings),
            "jobs": [result.to_dict() for result in self.jobs],
            "modules": [result.to_dict() for result in self.modules],
            "degrees": [result.to_dict() for result in self.degrees],
        }
