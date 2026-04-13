"use client";

import { useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";

import { ResultCard } from "@/components/result-card";
import {
  DegreeRecommendation,
  ExplorerResponse,
  JobRecommendation,
  ModuleRecommendation,
} from "@/lib/types";

const transport = new DefaultChatTransport({
  api: "/api/chat",
  body: () => ({
    topJobs: 3,
    topModules: 3,
    topDegrees: 3,
  }),
});

const SAMPLE_PROMPTS: { label: string; text: string }[] = [
  {
    label: "Data analyst · SQL & dashboards",
    text: "Find data analyst jobs that emphasise SQL, dashboards, and experimentation.",
  },
  {
    label: "Courses for cybersecurity roles",
    text: "Which NUS courses are most relevant to cybersecurity analyst roles?",
  },
  { label: "Mechanical Engineer", text: "Mechanical Engineer" },
  { label: "CS2040", text: "CS2040" },
];

type AlignmentReportPart = {
  type: "data-alignment-report";
  data: ExplorerResponse;
};

type TextPart = {
  type: "text";
  text: string;
};

function isTextPart(part: unknown): part is TextPart {
  return (
    typeof part === "object" &&
    part !== null &&
    "type" in part &&
    "text" in part &&
    (part as { type?: string }).type === "text"
  );
}

function isAlignmentReportPart(part: unknown): part is AlignmentReportPart {
  return (
    typeof part === "object" &&
    part !== null &&
    "type" in part &&
    "data" in part &&
    (part as { type?: string }).type === "data-alignment-report"
  );
}

function ResultSection({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow: string;
  children: React.ReactNode;
}) {
  return (
    <section className="result-section">
      <div className="section-heading">
        <p className="section-heading__eyebrow">{eyebrow}</p>
        <h4>{title}</h4>
      </div>
      <div className="result-section__grid">{children}</div>
    </section>
  );
}

function renderReport(report: ExplorerResponse, keyPrefix: string) {
  return (
    <div className="alignment-report" key={`${keyPrefix}-report`}>
      {report.matchedEntity ? (
        <div className="matched-banner">
          <span className="matched-banner__label">Matched</span>
          <strong>{report.matchedEntity.label}</strong>
        </div>
      ) : null}

      {report.jobs.length > 0 ? (
        <ResultSection
          eyebrow="Job Ads"
          title="Closest MyCareersFuture matches"
        >
          {report.jobs.map((result: JobRecommendation) => (
            <ResultCard
              key={`${keyPrefix}-job-${result.jobId}`}
              kind="jobs"
              result={result}
            />
          ))}
        </ResultSection>
      ) : null}

      {report.modules.length > 0 ? (
        <ResultSection eyebrow="Courses" title="Relevant NUS courses">
          {report.modules.map((result: ModuleRecommendation) => (
            <ResultCard
              key={`${keyPrefix}-module-${result.moduleCode}`}
              kind="modules"
              result={result}
            />
          ))}
        </ResultSection>
      ) : null}

      {report.degrees.length > 0 ? (
        <ResultSection eyebrow="Degree Fit" title="Aligned degree programmes">
          {report.degrees.map((result: DegreeRecommendation) => (
            <ResultCard
              key={`${keyPrefix}-degree-${result.degreeId}-${result.degreeLabel}`}
              kind="degrees"
              result={result}
            />
          ))}
        </ResultSection>
      ) : null}

      {report.warnings.length > 0 ? (
        <ul className="warning-list">
          {report.warnings.map((warning) => (
            <li key={`${keyPrefix}-${warning}`}>{warning}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export function ChatClient() {
  const [input, setInput] = useState("");
  const { messages, sendMessage, status, error } = useChat({ transport });

  const busy = status === "submitted" || status === "streaming";

  function sendFromInput() {
    const text = input.trim();
    if (!text || busy) {
      return;
    }
    sendMessage({ text });
    setInput("");
  }

  return (
    <section className="chat-shell">
      <section className="transcript">
        <div className="empty-state">
          <div className="empty-state__badge">MOE Officer Copilot</div>
          <h3>
            Search job ads in natural language and inspect course fit instantly
          </h3>
          <p>
            The assistant searches the filtered MyCareersFuture corpus,
            recommends relevant NUS courses, highlights aligned degree
            programmes, and can turn those retrieval results into a grounded
            natural-language explanation.
          </p>
        </div>

        {messages.map((message) => {
          const textParts = message.parts?.filter(isTextPart) ?? [];
          const reportParts =
            message.parts?.filter(isAlignmentReportPart) ?? [];

          return (
            <article
              className={
                message.role === "user"
                  ? "message message--user"
                  : "message message--assistant"
              }
              key={message.id}
            >
              <div className="message__meta">
                {message.role === "user" ? "You" : "MOE Officer Copilot"}
              </div>
              {textParts.map((part, index) => (
                <p
                  className="message__text"
                  key={`${message.id}-text-${index}`}
                >
                  {part.text}
                </p>
              ))}
              {reportParts.map((part, index) =>
                renderReport(part.data, `${message.id}-${index}`),
              )}
            </article>
          );
        })}
      </section>

      <form
        className="composer"
        onSubmit={(event) => {
          event.preventDefault();
          sendFromInput();
        }}
      >
        <div className="composer__panel">
          <textarea
            aria-label="Chat input"
            className="composer__input"
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key !== "Enter" || event.shiftKey) {
                return;
              }
              event.preventDefault();
              sendFromInput();
            }}
            placeholder="Ask about a role, paste a job description, or enter a degree name / module code..."
            rows={5}
            value={input}
          />
        </div>
        <div className="composer__suggestions" aria-label="Sample prompts">
          <span className="composer__suggestions-label">Try</span>
          <div className="composer__suggestions-track">
            {SAMPLE_PROMPTS.map(({ label, text }) => (
              <button
                className="prompt-chip prompt-chip--compact"
                key={text}
                onClick={() => setInput(text)}
                title={text}
                type="button"
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="composer__footer">
          <span className="helper">
            {status === "submitted" || status === "streaming"
              ? "Searching jobs, courses, degree profiles, and composing a grounded summary..."
              : "The app uses notebook-derived retrieval signals first, then optionally adds an LLM-written explanation."}
          </span>
          <button
            className="send-button"
            disabled={!input.trim() || busy}
            type="submit"
          >
            Explore
          </button>
        </div>
        {error ? <p className="error-text">{error.message}</p> : null}
      </form>
    </section>
  );
}
