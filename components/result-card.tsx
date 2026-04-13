"use client";

import {
  DegreeRecommendation,
  JobRecommendation,
  ModuleRecommendation,
} from "@/lib/types";

type ResultCardProps =
  | { result: JobRecommendation; kind: "jobs" }
  | { result: ModuleRecommendation; kind: "modules" }
  | { result: DegreeRecommendation; kind: "degrees" };

/** Reasons repeated for every row in explore mode — section headings already explain retrieval. */
const GENERIC_RESULT_REASONS = new Set([
  "Semantically similar to your natural-language query within the filtered MyCareersFuture corpus.",
  "Course content is semantically aligned to the role, skills, or job description you provided.",
  "Degree profile is semantically aligned to the role or skill mix described in your query.",
]);

function formatMatchPercent(score: number): string {
  const pct = Math.round(Math.max(0, Math.min(1, score)) * 100);
  return `${pct}% match`;
}

function ScorePill({ score }: { score: number }) {
  return (
    <span className="score-pill" title={`Score ${score.toFixed(4)}`}>
      {formatMatchPercent(score)}
    </span>
  );
}

export function ResultCard(props: ResultCardProps) {
  if (props.kind === "jobs") {
    const result = props.result;
    const showReason = !GENERIC_RESULT_REASONS.has(result.reason);
    return (
      <article className="result-card result-card--job">
        <div className="result-card__header">
          <div className="result-card__title-block">
            <h4 className="result-card__title" title={result.title}>
              {result.title}
            </h4>
            <p className="result-card__subtitle">
              {result.company || "Unknown company"}
            </p>
          </div>
          <ScorePill score={result.score} />
        </div>
        {result.categories.length > 0 ? (
          <div className="tag-row">
            {result.categories.map((category) => (
              <span className="tag" key={category}>
                {category}
              </span>
            ))}
          </div>
        ) : null}
        {showReason ? (
          <p className="result-card__reason">{result.reason}</p>
        ) : null}
        {result.descriptionSnippet ? (
          <p className="result-card__snippet">{result.descriptionSnippet}</p>
        ) : null}
        {result.url ? (
          <div className="result-card__footer">
            <a
              className="result-link"
              href={result.url}
              target="_blank"
              rel="noreferrer"
            >
              Open listing
            </a>
          </div>
        ) : null}
      </article>
    );
  }

  if (props.kind === "modules") {
    const result = props.result;
    const heading = `${result.moduleCode} · ${result.title}`;
    const showReason = !GENERIC_RESULT_REASONS.has(result.reason);
    return (
      <article className="result-card result-card--module">
        <div className="result-card__header">
          <div className="result-card__title-block">
            <h4 className="result-card__title" title={heading}>
              <span className="result-card__code">{result.moduleCode}</span>
              <span className="result-card__title-sep" aria-hidden="true">
                {" · "}
              </span>
              {result.title}
            </h4>
            <p className="result-card__subtitle">{result.context}</p>
          </div>
          <ScorePill score={result.score} />
        </div>
        {showReason ? (
          <p className="result-card__reason">{result.reason}</p>
        ) : null}
        {result.descriptionSnippet ? (
          <p className="result-card__snippet">{result.descriptionSnippet}</p>
        ) : null}
      </article>
    );
  }

  const result = props.result;
  const showReason = !GENERIC_RESULT_REASONS.has(result.reason);
  const score =
    typeof result.score === "number" && Number.isFinite(result.score)
      ? result.score
      : null;
  return (
    <article className="result-card result-card--degree">
      <div className="result-card__header">
        <div className="result-card__title-block">
          <h4 className="result-card__title" title={result.degreeLabel}>
            {result.degreeLabel}
          </h4>
          <p className="result-card__subtitle">
            {result.moduleCount > 0
              ? `${result.moduleCount} curated courses in the notebook profile`
              : "Curriculum profile"}
          </p>
        </div>
        {score !== null ? (
          <ScorePill score={score} />
        ) : (
          <span className="score-pill score-pill--static">Aligned</span>
        )}
      </div>
      {showReason ? (
        <p className="result-card__reason">{result.reason}</p>
      ) : null}
    </article>
  );
}
