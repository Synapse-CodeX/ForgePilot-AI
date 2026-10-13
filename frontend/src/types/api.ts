// ──────────────────────────────────────────────────────────────
// ForgePilot AI — TypeScript API types (matching backend schemas)
// ──────────────────────────────────────────────────────────────

export interface HealthStatus {
  status: string;
  service: string;
}

export interface RepairRequest {
  repository_url: string;
  issue_number: number;
}

// ── Workflow ───────────────────────────────────────────────────

export type WorkflowStatus = 'succeeded' | 'failed' | 'validation_failed';
export type StageStatus = 'succeeded' | 'failed' | 'pending' | 'running';

export type StageName =
  | 'repository_inspection'
  | 'repository_analysis'
  | 'root_cause_analysis'
  | 'patch_generation'
  | 'patch_validation';

export interface WorkflowStageResult {
  stage: StageName;
  status: StageStatus;
  message: string;
  duration_seconds: number;
  error_type?: string;
}

export interface RepairWorkflowResult {
  repository_full_name: string;
  issue_number: number;
  status: WorkflowStatus;
  stages: WorkflowStageResult[];
  repository?: RepositoryContext;
  issue?: IssueContext;
  repository_analysis?: RepositoryAnalysis;
  root_cause?: RootCauseAnalysis;
  patch_proposal?: PatchProposal;
  patch_application?: PatchApplicationResult;
  validation_report?: ValidationReport;
  summary?: string;
}

// ── Repository ─────────────────────────────────────────────────

export interface RepositoryContext {
  owner: string;
  name: string;
  full_name: string;
  html_url: string;
  description?: string;
  default_branch?: string;
  private: boolean;
  language?: string;
  stars: number;
  forks: number;
  open_issues: number;
}

// ── Issue ──────────────────────────────────────────────────────

export interface IssueContext {
  repository_full_name: string;
  number: number;
  title: string;
  body?: string;
  state: string;
  html_url: string;
  author?: string;
  labels: string[];
  created_at?: string;
  updated_at?: string;
  is_pull_request: boolean;
}

// ── Repository Analysis ────────────────────────────────────────

export interface AnalyzedFile {
  path: string;
  score: number;
  reasons: string[];
  definitions: string[];
  imports: string[];
  syntax_valid: boolean;
}

export interface RepositoryAnalysis {
  repository_full_name: string;
  issue_number: number;
  issue_title: string;
  files_scanned: number;
  candidates: AnalyzedFile[];
}

// ── Root Cause ─────────────────────────────────────────────────

export interface RootCauseEvidence {
  file_path: string;
  observation: string;
  code_reference?: string;
}

export interface RootCauseAnalysis {
  repository_full_name: string;
  issue_number: number;
  issue_title: string;
  root_cause: string;
  confidence: number; // 0–1
  summary: string;
  evidence: RootCauseEvidence[];
  recommended_files: string[];
}

// ── Patch ──────────────────────────────────────────────────────

export interface PatchProposal {
  repository_full_name: string;
  issue_number: number;
  summary: string;
  rationale: string;
  unified_diff: string;
  files_changed: string[];
}

export interface PatchApplicationResult {
  repository_full_name: string;
  issue_number: number;
  applied: boolean;
  files_changed: string[];
  message: string;
}

// ── Validation ─────────────────────────────────────────────────

export interface ValidationCommandResult {
  profile: string;
  command: string;
  passed: boolean;
  exit_code: number;
  stdout: string;
  stderr: string;
  duration_seconds: number;
  timed_out: boolean;
}

export interface ValidationReport {
  repository_full_name: string;
  issue_number: number;
  passed: boolean;
  results: ValidationCommandResult[];
  summary: string;
}
