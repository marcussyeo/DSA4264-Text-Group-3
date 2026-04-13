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
  descriptionSnippet: string;
  url?: string | null;
}

export interface ModuleRecommendation {
  moduleCode: string;
  title: string;
  context: string;
  score: number;
  reason: string;
  descriptionSnippet: string;
}

export interface DegreeRecommendation {
  degreeId: string;
  degreeLabel: string;
  score?: number | null;
  reason: string;
  moduleCount: number;
}

export interface SearchResponse {
  mode: SearchMode;
  normalizedQuery: string;
  matchedEntity?: MatchedEntity | null;
  warnings: string[];
  results: Array<JobRecommendation | ModuleRecommendation>;
}

export type ExplorerIntent = "module_lookup" | "degree_lookup" | "job_query";

export interface ExplorerResponse {
  intent: ExplorerIntent;
  normalizedQuery: string;
  matchedEntity?: MatchedEntity | null;
  warnings: string[];
  jobs: JobRecommendation[];
  modules: ModuleRecommendation[];
  degrees: DegreeRecommendation[];
}

export interface ChatRequestBody {
  topJobs?: number;
  topModules?: number;
  topDegrees?: number;
  messages?: Array<{
    role: string;
    parts?: Array<{ type: string; text?: string }>;
  }>;
}
