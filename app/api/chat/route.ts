import { createUIMessageStream, createUIMessageStreamResponse } from "ai";

import { buildFallbackNarrative, generateGroundedNarrative } from "@/lib/llm";
import { runAlignmentExplorer } from "@/lib/search-api";
import { ChatRequestBody, ExplorerResponse } from "@/lib/types";

export const maxDuration = 30;

function extractLatestUserText(
  messages: Array<{ role?: string; parts?: Array<Record<string, unknown>> }>,
): string {
  const latestUserMessage = [...messages]
    .reverse()
    .find((message) => message.role === "user");
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

function buildSummary(result: ExplorerResponse): string {
  if (
    result.jobs.length === 0 &&
    result.modules.length === 0 &&
    result.degrees.length === 0
  ) {
    return (
      result.warnings[0] ??
      "I couldn't find a useful alignment result for that query."
    );
  }

  if (result.intent === "degree_lookup" && result.matchedEntity) {
    return `I matched ${result.matchedEntity.label} to the curated degree profile and pulled the strongest job ads plus representative courses from its curriculum basket.`;
  }

  if (result.intent === "module_lookup" && result.matchedEntity) {
    return `I matched ${result.matchedEntity.label} to an exact NUS course, then surfaced nearby job ads and the degree baskets that include it.`;
  }

  return `I found ${result.jobs.length} job ads, ${result.modules.length} relevant NUS courses, and ${result.degrees.length} aligned degree programmes for your query.`;
}

export async function POST(request: Request) {
  const body = (await request.json()) as ChatRequestBody;
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

  const explorerResponse = await runAlignmentExplorer(
    query,
    body.topJobs ?? 3,
    body.topModules ?? 3,
    body.topDegrees ?? 3,
  );
  const textId = "alignment-summary";

  return createUIMessageStreamResponse({
    stream: createUIMessageStream({
      execute: async ({ writer }) => {
        const summary = buildSummary(explorerResponse);
        let narrative: string;
        let replySource: "llm" | "fallback";

        try {
          narrative = await generateGroundedNarrative(query, explorerResponse);
          replySource = "llm";
          if (narrative.trim()) {
            console.log("[chat] narrative: llm", {
              preview: narrative.slice(0, 120),
            });
          } else {
            console.log(
              "[chat] narrative: llm returned empty; will use buildSummary if needed",
            );
          }
        } catch (err) {
          narrative = buildFallbackNarrative(query, explorerResponse);
          replySource = "fallback";
          console.warn("[chat] narrative: fallback (LLM threw)", {
            message: err instanceof Error ? err.message : String(err),
            preview: narrative.slice(0, 120),
          });
        }

        const responseText = narrative.trim() || summary;
        const usedSummary = responseText === summary;
        console.log("[chat] reply outcome", {
          replySource,
          usedSummary,
        });

        writer.write({
          type: "text-start",
          id: textId,
        });
        writer.write({
          type: "text-delta",
          id: textId,
          delta: responseText,
        });
        writer.write({
          type: "text-end",
          id: textId,
        });

        writer.write({
          type: "data-alignment-report",
          data: explorerResponse,
        });
      },
    }),
  });
}
