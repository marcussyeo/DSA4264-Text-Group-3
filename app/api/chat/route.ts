import { createUIMessageStream, createUIMessageStreamResponse } from "ai";

import { runSearch } from "@/lib/search-api";
import { ChatRequestBody, SearchMode, SearchResponse } from "@/lib/types";

export const maxDuration = 30;

function extractLatestUserText(
  messages: Array<{ role?: string; parts?: Array<Record<string, unknown>> }>,
): string {
  const latestUserMessage = [...messages].reverse().find((message) => message.role === "user");
  if (!latestUserMessage) {
    return "";
  }

  return (
    latestUserMessage.parts
      ?.map((part) => {
        if (part.type === "text" && typeof part.text === "string") {
          return part.text;
        }
        return "";
      })
      .join(" ")
      .trim() ?? ""
  );
}

function buildSummary(mode: SearchMode, result: SearchResponse): string {
  if (result.results.length === 0) {
    return result.warnings[0] ?? "No results found.";
  }

  const noun = mode === "find_jobs" ? "job listings" : "modules";
  const entityLabel = result.matchedEntity?.label ?? result.normalizedQuery;
  return `Here are the top ${result.results.length} ${noun} for ${entityLabel}.`;
}

export async function POST(request: Request) {
  const body = (await request.json()) as ChatRequestBody;
  const mode: SearchMode = body.mode ?? "find_jobs";
  const topK = body.topK ?? 8;
  const messages = body.messages ?? [];
  const query = extractLatestUserText(messages);

  if (!query) {
    return new Response(JSON.stringify({ error: "Missing user query." }), {
      status: 400,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  const searchResponse = await runSearch(mode, query, topK);
  const summary = buildSummary(mode, searchResponse);
  const textId = "search-summary";

  return createUIMessageStreamResponse({
    stream: createUIMessageStream({
      execute: async ({ writer }) => {
        writer.write({
          type: "text-start",
          id: textId,
        });
        writer.write({
          type: "text-delta",
          id: textId,
          delta: summary,
        });
        writer.write({
          type: "text-end",
          id: textId,
        });
        writer.write({
          type: "data-search-results",
          data: searchResponse,
        });
      },
    }),
  });
}
