import { ExplorerResponse } from "@/lib/types";

const OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses";
const DEFAULT_OPENAI_MODEL = process.env.OPENAI_MODEL ?? "gpt-5.4-mini";
const DEFAULT_REASONING_EFFORT = process.env.OPENAI_REASONING_EFFORT ?? "low";

type OpenAIResponseContentPart = {
  type?: string;
  text?: string;
};

type OpenAIResponseOutputItem = {
  content?: OpenAIResponseContentPart[];
};

type OpenAIResponsesPayload = {
  output_text?: string;
  output?: OpenAIResponseOutputItem[];
  error?: {
    message?: string;
  };
};

function hasOpenAIConfig(): boolean {
  return Boolean(process.env.OPENAI_API_KEY);
}

function pickFirst<T>(items: T[], count: number): T[] {
  return items.slice(0, count);
}

function buildEvidencePayload(query: string, result: ExplorerResponse) {
  return {
    query,
    intent: result.intent,
    matchedEntity: result.matchedEntity ?? null,
    warnings: result.warnings,
    jobs: pickFirst(result.jobs, 3).map((job) => ({
      title: job.title,
      company: job.company,
      score: Number(job.score.toFixed(4)),
      categories: job.categories,
      reason: job.reason,
      descriptionSnippet: job.descriptionSnippet,
    })),
    modules: pickFirst(result.modules, 3).map((module) => ({
      moduleCode: module.moduleCode,
      title: module.title,
      context: module.context,
      score: Number(module.score.toFixed(4)),
      reason: module.reason,
      descriptionSnippet: module.descriptionSnippet,
    })),
    degrees: pickFirst(result.degrees, 3).map((degree) => ({
      degreeLabel: degree.degreeLabel,
      moduleCount: degree.moduleCount,
      score:
        typeof degree.score === "number" ? Number(degree.score.toFixed(4)) : null,
      reason: degree.reason,
    })),
  };
}

function extractOutputText(payload: OpenAIResponsesPayload): string {
  if (typeof payload.output_text === "string" && payload.output_text.trim()) {
    return payload.output_text.trim();
  }

  return (
    payload.output
      ?.flatMap((item) => item.content ?? [])
      .map((part) => (typeof part.text === "string" ? part.text : ""))
      .join("")
      .trim() ?? ""
  );
}

function formatList(values: string[]): string {
  return values.filter(Boolean).join(", ");
}

export function buildFallbackNarrative(
  query: string,
  result: ExplorerResponse,
): string {
  if (
    result.jobs.length === 0 &&
    result.modules.length === 0 &&
    result.degrees.length === 0
  ) {
    return (
      result.warnings[0] ??
      `I couldn't find enough grounded evidence to answer "${query}" from the current retrieval indexes.`
    );
  }

  const topJob = result.jobs[0];
  const topModule = result.modules[0];
  const topDegree = result.degrees[0];

  const lead =
    result.matchedEntity?.label != null
      ? `I grounded this answer on the matched entity "${result.matchedEntity.label}" and the strongest retrieved evidence.`
      : `I grounded this answer on the strongest retrieved evidence for "${query}".`;

  const details = [
    topJob
      ? `The clearest job signal is ${topJob.title} at ${topJob.company || "an unknown employer"}${topJob.categories.length > 0 ? ` in ${formatList(topJob.categories)}` : ""}.`
      : "",
    topModule
      ? `The closest module match is ${topModule.moduleCode} ${topModule.title}.`
      : "",
    topDegree
      ? `The most aligned degree profile is ${topDegree.degreeLabel}${topDegree.moduleCount > 0 ? ` with ${topDegree.moduleCount} curated modules in its basket` : ""}.`
      : "",
  ]
    .filter(Boolean)
    .join(" ");

  const warnings =
    result.warnings.length > 0
      ? ` Note: ${result.warnings.join(" ")}`
      : "";

  return `${lead}\n\n${details}${warnings}`.trim();
}

export async function generateGroundedNarrative(
  query: string,
  result: ExplorerResponse,
): Promise<string> {
  if (!hasOpenAIConfig()) {
    return buildFallbackNarrative(query, result);
  }

  const response = await fetch(OPENAI_RESPONSES_URL, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: DEFAULT_OPENAI_MODEL,
      reasoning: {
        effort: DEFAULT_REASONING_EFFORT,
      },
      instructions:
        "You are MOE Officer Copilot, a grounded analyst for curriculum-job alignment. Use only the supplied retrieval evidence. Do not invent facts, courses, jobs, or employers. If the evidence is weak, say that clearly. Keep the answer concise: two short paragraphs maximum. Mention specific module codes, degree labels, or job titles only when they are in the evidence.",
      input: `User query: ${query}\n\nRetrieved evidence:\n${JSON.stringify(
        buildEvidencePayload(query, result),
        null,
        2,
      )}\n\nWrite a concise answer that explains the strongest alignment signals, the main caveat or warning if any, and what the user should look at first in the retrieved results.`,
    }),
    cache: "no-store",
  });

  const payload = (await response.json()) as OpenAIResponsesPayload;
  if (!response.ok) {
    const message =
      payload.error?.message ?? "The OpenAI response request failed.";
    throw new Error(message);
  }

  const text = extractOutputText(payload);
  if (!text) {
    throw new Error("The OpenAI response did not include any text.");
  }

  return text;
}
