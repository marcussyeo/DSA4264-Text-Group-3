import { ExplorerResponse, SearchMode, SearchResponse } from "@/lib/types";

const DEFAULT_RETRIEVAL_API_BASE_URL =
  process.env.RETRIEVAL_API_BASE_URL ?? "http://127.0.0.1:8000";

function endpointForMode(mode: SearchMode): string {
  return mode === "find_jobs" ? "/search/jobs" : "/search/modules";
}

export async function runSearch(
  mode: SearchMode,
  query: string,
  topK = 8,
): Promise<SearchResponse> {
  const response = await fetch(
    `${DEFAULT_RETRIEVAL_API_BASE_URL}${endpointForMode(mode)}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        topK,
      }),
      cache: "no-store",
    },
  );

  const payload = (await response.json()) as SearchResponse | { error: string };
  if (!response.ok) {
    const message =
      "error" in payload ? payload.error : "The retrieval service request failed.";
    throw new Error(message);
  }

  return payload as SearchResponse;
}

export async function runAlignmentExplorer(
  query: string,
  topJobs = 3,
  topModules = 3,
  topDegrees = 3,
): Promise<ExplorerResponse> {
  const response = await fetch(`${DEFAULT_RETRIEVAL_API_BASE_URL}/search/explore`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      topJobs,
      topModules,
      topDegrees,
    }),
    cache: "no-store",
  });

  const payload = (await response.json()) as ExplorerResponse | { error: string };
  if (!response.ok) {
    const message =
      "error" in payload ? payload.error : "The retrieval service request failed.";
    throw new Error(message);
  }

  return payload as ExplorerResponse;
}
