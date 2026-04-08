"use client";

import { useMemo, useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";

import { ResultCard } from "@/components/result-card";
import {
  JobRecommendation,
  ModuleRecommendation,
  SearchMode,
  SearchResponse,
} from "@/lib/types";

type SearchDataPart = {
  type: "data-search-results";
  data: SearchResponse;
};

type TextPart = {
  type: "text";
  text: string;
};

const MODE_OPTIONS: Array<{ value: SearchMode; label: string; helper: string }> = [
  {
    value: "find_jobs",
    label: "Find jobs",
    helper: "Enter a NUS module code like CS1010 or a degree label like Computer Science.",
  },
  {
    value: "find_modules",
    label: "Find modules",
    helper: "Enter a job title or paste a job description to retrieve relevant modules.",
  },
];

function isTextPart(part: unknown): part is TextPart {
  return (
    typeof part === "object" &&
    part !== null &&
    "type" in part &&
    "text" in part &&
    (part as { type?: string }).type === "text"
  );
}

function isSearchDataPart(part: unknown): part is SearchDataPart {
  return (
    typeof part === "object" &&
    part !== null &&
    "type" in part &&
    "data" in part &&
    (part as { type?: string }).type === "data-search-results"
  );
}

function isJobRecommendation(
  result: JobRecommendation | ModuleRecommendation,
): result is JobRecommendation {
  return "jobId" in result;
}

function isModuleRecommendation(
  result: JobRecommendation | ModuleRecommendation,
): result is ModuleRecommendation {
  return "moduleCode" in result;
}

export function ChatClient() {
  const [mode, setMode] = useState<SearchMode>("find_jobs");
  const [input, setInput] = useState("");

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: "/api/chat",
        body: () => ({
          mode,
          topK: 8,
        }),
      }),
    [mode],
  );

  const { messages, sendMessage, status, error } = useChat({
    transport,
  });

  const currentMode = MODE_OPTIONS.find((option) => option.value === mode)!;

  return (
    <div className="chat-shell">
      <section className="control-panel">
        <div>
          <p className="eyebrow">Mode</p>
          <h2>{currentMode.label}</h2>
          <p className="helper">{currentMode.helper}</p>
        </div>
        <div className="toggle-row" role="tablist" aria-label="Search mode">
          {MODE_OPTIONS.map((option) => (
            <button
              className={option.value === mode ? "mode-pill mode-pill--active" : "mode-pill"}
              key={option.value}
              onClick={() => setMode(option.value)}
              type="button"
            >
              {option.label}
            </button>
          ))}
        </div>
      </section>

      <section className="transcript">
        {messages.length === 0 ? (
          <div className="empty-state">
            <h3>Start a retrieval chat</h3>
            <p>
              This interface keeps the conversation format familiar, but every turn is a deterministic
              retrieval request against your NUS and MyCareersFuture index.
            </p>
          </div>
        ) : null}

        {messages.map((message) => {
          const textParts = message.parts?.filter(isTextPart) ?? [];
          const searchParts = message.parts?.filter(isSearchDataPart) ?? [];

          return (
            <article
              className={message.role === "user" ? "message message--user" : "message message--assistant"}
              key={message.id}
            >
              <div className="message__meta">{message.role === "user" ? "You" : "Assistant"}</div>
              {textParts.map((part, index) => (
                <p className="message__text" key={`${message.id}-text-${index}`}>
                  {part.text}
                </p>
              ))}
              {searchParts.map((part, index) => (
                <div className="result-group" key={`${message.id}-results-${index}`}>
                  {part.data.matchedEntity ? (
                    <p className="result-group__label">
                      Matched entity: <strong>{part.data.matchedEntity.label}</strong>
                    </p>
                  ) : null}
                  {part.data.results.map((result) =>
                    part.data.mode === "find_jobs" && isJobRecommendation(result) ? (
                      <ResultCard
                        key={`${message.id}-${result.jobId}`}
                        mode="find_jobs"
                        result={result}
                      />
                    ) : part.data.mode === "find_modules" && isModuleRecommendation(result) ? (
                      <ResultCard
                        key={`${message.id}-${result.moduleCode}`}
                        mode="find_modules"
                        result={result}
                      />
                    ) : null
                  )}
                  {part.data.warnings.length > 0 ? (
                    <ul className="warning-list">
                      {part.data.warnings.map((warning) => (
                        <li key={warning}>{warning}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              ))}
            </article>
          );
        })}
      </section>

      <form
        className="composer"
        onSubmit={(event) => {
          event.preventDefault();
          const text = input.trim();
          if (!text) {
            return;
          }
          sendMessage(
            {
              text,
            },
            {
              body: {
                mode,
                topK: 8,
              },
            },
          );
          setInput("");
        }}
      >
        <textarea
          aria-label="Chat input"
          className="composer__input"
          onChange={(event) => setInput(event.target.value)}
          placeholder={
            mode === "find_jobs"
              ? "Try CS1010 or Computer Science"
              : "Try Data Analyst or paste a job description"
          }
          rows={4}
          value={input}
        />
        <div className="composer__footer">
          <span className="helper">
            {status === "submitted" || status === "streaming"
              ? "Searching..."
              : "Results are deterministic and come from the retrieval backend."}
          </span>
          <button className="send-button" disabled={!input.trim() || status === "submitted" || status === "streaming"} type="submit">
            Send
          </button>
        </div>
        {error ? <p className="error-text">{error.message}</p> : null}
      </form>
    </div>
  );
}
