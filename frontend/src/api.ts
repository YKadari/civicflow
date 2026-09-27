import type {
  Approval,
  CaseAnalysis,
  CaseContext,
  CaseSummary,
  CitizenRequestResponse,
  EvaluationReport,
  PolicyReplayBatchResult,
  PolicyReplayResult,
} from "./types";


const API_BASE =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000";


async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${API_BASE}${path}`,
    {
      ...options,

      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    },
  );

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const body = await response.json();

      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // Keep fallback error.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}


export const api = {
  async health(): Promise<boolean> {
    await request(
      "/health",
    );

    return true;
  },


  listCases(): Promise<CaseSummary[]> {
    return request(
      "/cases",
    );
  },


  getCase(
    caseId: string,
  ): Promise<CaseContext> {
    return request(
      `/cases/${encodeURIComponent(caseId)}`,
    );
  },


  createRequest(
    caseId: string,
    description: string,
  ): Promise<CitizenRequestResponse> {
    return request(
      `/cases/${encodeURIComponent(caseId)}/requests`,
      {
        method: "POST",

        body: JSON.stringify({
          description,
        }),
      },
    );
  },


  analyze(
    caseId: string,
    eventId: string,
  ): Promise<CaseAnalysis> {
    return request(
      `/cases/${encodeURIComponent(caseId)}/analyze`,
      {
        method: "POST",

        body: JSON.stringify({
          event_id: eventId,
        }),
      },
    );
  },


  listApprovals(
    status?: string,
    caseId?: string,
  ): Promise<Approval[]> {
    const params =
      new URLSearchParams();

    if (status) {
      params.set(
        "status",
        status,
      );
    }

    if (caseId) {
      params.set(
        "case_id",
        caseId,
      );
    }

    const query =
      params.toString();

    return request(
      `/approvals${query ? `?${query}` : ""}`,
    );
  },


  approve(
    approvalId: string,
    reviewer: string,
  ): Promise<Approval> {
    return request(
      `/approvals/${encodeURIComponent(approvalId)}/approve`,
      {
        method: "POST",

        body: JSON.stringify({
          reviewer,
        }),
      },
    );
  },


  reject(
    approvalId: string,
    reviewer: string,
  ): Promise<Approval> {
    return request(
      `/approvals/${encodeURIComponent(approvalId)}/reject`,
      {
        method: "POST",

        body: JSON.stringify({
          reviewer,
        }),
      },
    );
  },


  replayCase(
    caseId: string,
    action: string,
    baselineVersion: number,
    candidateVersion: number,
  ): Promise<PolicyReplayResult> {
    return request(
      "/policy-replay",
      {
        method: "POST",

        body: JSON.stringify({
          case_id: caseId,
          action,
          baseline_version:
            baselineVersion,
          candidate_version:
            candidateVersion,
        }),
      },
    );
  },


  replayBatch(
    action: string,
    baselineVersion: number,
    candidateVersion: number,
  ): Promise<PolicyReplayBatchResult> {
    return request(
      "/policy-replay/batch",
      {
        method: "POST",

        body: JSON.stringify({
          action,
          baseline_version:
            baselineVersion,
          candidate_version:
            candidateVersion,
        }),
      },
    );
  },


  evaluation(): Promise<EvaluationReport> {
    return request(
      "/evaluation",
    );
  },
};