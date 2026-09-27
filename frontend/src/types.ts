export interface CaseSummary {
  case_id: string;
  citizen_id: string;
  program: string;
  status: string;
  created_at: string;
}


export interface Citizen {
  citizen_id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
}


export interface Payment {
  payment_id: string;
  amount: string;
  scheduled_date: string;
  paid_date: string | null;
  status: string;
}


export interface DocumentRecord {
  document_id: string;
  document_type: string;
  file_name: string;
  uploaded_at: string;
  review_status: string;
}


export interface CaseEvent {
  event_id: string;
  event_type: string;
  description: string | null;
  created_at: string;
}


export interface Approval {
  approval_id: string;
  case_id: string;
  action_type: string;
  status: string;
  requested_at: string;
  decided_at: string | null;
  reviewer: string | null;
}


export interface CaseContext {
  case: CaseSummary;
  citizen: Citizen;
  payments: Payment[];
  documents: DocumentRecord[];
  events: CaseEvent[];
  approvals: Approval[];
}


export interface CitizenRequestResponse {
  event_id: string;
  event_type: string;
  description: string | null;
  created_at: string;
}


export interface PolicyEvidence {
  chunk_id: string;
  policy_id: string;
  version: number;
  section: string;
  content: string;
  similarity: number;
}


export interface PaymentCheckResult {
  success: boolean;
  case_id: string;
  payments: Payment[];
  message: string;
}


export interface CaseAnalysis {
  case_id: string;
  request_type: string;
  facts: string[];

  recommended_action: string | null;

  classification_confidence: number | null;
  classification_source: string;

  requires_human_review: boolean;

  policy_evidence: PolicyEvidence[];

  recommendation_rationale: string | null;
  recommendation_confidence: number | null;

  cited_policy_chunks: string[];

  policy_check_allowed: boolean | null;
  policy_check_reasons: string[];

  decision_challenge_passed: boolean | null;
  challenge_verdict: string | null;
  challenge_reasons: string[];
  challenge_confidence: number | null;

  challenge_cited_policy_chunks: string[];
  challenge_missing_evidence: string[];

  challenged_action: string | null;

  tool_access_mode: string | null;
  tool_requires_approval: boolean | null;

  approval_request: Approval | null;

  executed_tool: string | null;

  payment_check_result: PaymentCheckResult | null;
}


export interface ReplayPolicyOutcome {
  policy_id: string;
  version: number;
  allowed: boolean;
  requires_human_review: boolean;
  reasons: string[];
}


export interface PolicyReplayResult {
  case_id: string;
  action: string;
  policy_id: string;

  baseline: ReplayPolicyOutcome;
  candidate: ReplayPolicyOutcome;

  outcome_changed: boolean;
  change_type: string;
}


export interface PolicyReplayBatchResult {
  action: string;
  policy_id: string;

  baseline_version: number;
  candidate_version: number;

  total_cases: number;
  changed_cases: number;
  unchanged_cases: number;

  results: PolicyReplayResult[];
}


export interface EvaluationMetric {
  name: string;
  passed: number;
  total: number;
  rate: number;
  description: string;
}


export interface EvaluationReport {
  dataset_cases: number;

  replay_changed_cases: number;
  replay_unchanged_cases: number;

  metrics: EvaluationMetric[];

  notes: string[];
}