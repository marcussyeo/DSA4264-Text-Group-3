"use client";

import { JobRecommendation, ModuleRecommendation } from "@/lib/types";

type ResultCardProps =
  | { result: JobRecommendation; mode: "find_jobs" }
  | { result: ModuleRecommendation; mode: "find_modules" };

export function ResultCard(props: ResultCardProps) {
  if (props.mode === "find_jobs") {
    const result = props.result;
    return (
      <article className="result-card">
        <div className="result-card__header">
          <div>
            <h4>{result.title}</h4>
            <p>{result.company || "Unknown company"}</p>
          </div>
          <span className="score-pill">{result.score.toFixed(4)}</span>
        </div>
        <p className="result-card__reason">{result.reason}</p>
        {result.categories.length > 0 ? (
          <div className="tag-row">
            {result.categories.map((category) => (
              <span className="tag" key={category}>
                {category}
              </span>
            ))}
          </div>
        ) : null}
        {result.url ? (
          <a
            className="result-link"
            href={result.url}
            target="_blank"
            rel="noreferrer"
          >
            Open listing
          </a>
        ) : null}
      </article>
    );
  }

  const result = props.result;
  return (
    <article className="result-card">
      <div className="result-card__header">
        <div>
          <h4>
            {result.moduleCode} - {result.title}
          </h4>
          <p>{result.department}</p>
        </div>
        <span className="score-pill">{result.score.toFixed(4)}</span>
      </div>
      <p className="result-card__reason">{result.reason}</p>
      <p className="result-card__snippet">{result.descriptionSnippet}</p>
    </article>
  );
}
