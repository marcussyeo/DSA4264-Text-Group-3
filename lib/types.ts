export type SearchMode = "find_jobs" | "find_modules";

export interface SearchRequest {
  mode: SearchMode;
  query: string;
  topK?: number;
}

export interface MatchedEntity {
  type: string;
  value: string;
  label: string;
}

export interface JobRecommendation {
  jobId: string;
  title: string;
  company: string;
  categories: string[];
  score: number;
  reason: string;
  url?: string | null;
}

export interface ModuleRecommendation {
  moduleCode: string;
  title: string;
  department: string;
  score: number;
  reason: string;
  descriptionSnippet: string;
}

export interface SearchResponse {
  mode: SearchMode;
  normalizedQuery: string;
  matchedEntity?: MatchedEntity | null;
  warnings: string[];
  results: Array<JobRecommendation | ModuleRecommendation>;
}

export interface ChatRequestBody {
  mode?: SearchMode;
  topK?: number;
  messages?: Array<{
    role: string;
    parts?: Array<{ type: string; text?: string }>;
  }>;
}
