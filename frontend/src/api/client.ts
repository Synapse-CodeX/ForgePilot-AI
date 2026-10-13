import type { HealthStatus, RepairRequest, RepairWorkflowResult } from '../types/api';

// ── Error class ────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ── Base URL ───────────────────────────────────────────────────

const BASE_URL: string = (import.meta.env.VITE_API_URL as string | undefined) ?? '';

// ── Generic request wrapper ────────────────────────────────────

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  let response: Response;

  try {
    response = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...(options?.headers ?? {}) },
      ...options,
    });
  } catch {
    throw new ApiError(
      `Network error: could not reach ${url}. Is the backend running?`,
    );
  }

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string; message?: string };
      message = body.detail ?? body.message ?? message;
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<T>;
}

// ── Endpoints ──────────────────────────────────────────────────

/** Health check — the only live endpoint. */
export async function checkHealth(): Promise<HealthStatus> {
  return request<HealthStatus>('/api/health');
}

/**
 * Start a repair workflow.
 * @throws {ApiError} Always — this endpoint is not yet implemented in the backend.
 */
export async function startRepair(_req: RepairRequest): Promise<never> {
  throw new ApiError(
    'Repair API endpoint not yet available. The backend repair workflow is under development.',
    501,
    'ENDPOINT_NOT_IMPLEMENTED',
  );
}

/**
 * Get the status/result of a running or completed repair job.
 * @throws {ApiError} Always — this endpoint is not yet implemented in the backend.
 */
export async function getRepairStatus(_jobId: string): Promise<RepairWorkflowResult> {
  throw new ApiError(
    'Repair status endpoint not yet available. The backend repair workflow is under development.',
    501,
    'ENDPOINT_NOT_IMPLEMENTED',
  );
}
