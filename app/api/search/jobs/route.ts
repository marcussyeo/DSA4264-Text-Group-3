import { NextResponse } from "next/server";

import { runSearch } from "@/lib/search-api";

export async function POST(request: Request) {
  const { query, topK } = (await request.json()) as { query?: string; topK?: number };

  if (!query) {
    return NextResponse.json({ error: "Missing query." }, { status: 400 });
  }

  try {
    const response = await runSearch("find_jobs", query, topK ?? 8);
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Request failed." },
      { status: 502 },
    );
  }
}
