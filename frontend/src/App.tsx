import {

  useEffect,

  useMemo,

  useState,

} from "react";



import type {

  FormEvent,

  ReactNode,

} from "react";



import { api } from "./api";



import type {

  Approval,

  CaseAnalysis,

  CaseContext,

  CaseSummary,

  EvaluationReport,

  PolicyReplayBatchResult,

  PolicyReplayResult,

} from "./types";





type Tab =

  | "cases"

  | "approvals"

  | "replay"

  | "evaluation";


type DemoScenario = {
  title: string;
  sidebarDescription: string;
  description: string;
  prompt: string;
  expected: string;
};

const DEMO_SCENARIOS: Record<string, DemoScenario> = {
  "CF-10001": {
    title: "Safe Payment Check",
    sidebarDescription: "Read-only automation",
    description: "Checks a missing payment without changing case state. This demonstrates the low-risk path through policy retrieval and the deterministic tool gate.",
    prompt: "My housing assistance payment has not arrived. Can you check what happened?",
    expected: "Check Payment → Policy allowed → Read-only tool executes",
  },
  "CF-10002": {
    title: "Safety Challenge",
    sidebarDescription: "Insufficient evidence is challenged",
    description: "Requests a consequential investigation when required timing and verification evidence is incomplete. CivicFlow should stop the action for human review.",
    prompt: "My housing assistance payment is missing. Please open a formal investigation into why I have not received it.",
    expected: "Open Investigation → Policy allowed → Decision Challenge blocks",
  },
  "CF-10003": {
    title: "Human Approval",
    sidebarDescription: "Consequential action is gated",
    description: "Uses a case where the investigation prerequisites are established. The independent challenge should pass, but CivicFlow still requires human approval before a state-changing action can proceed.",
    prompt: "My housing assistance payment is missing. Please open a formal investigation into why I have not received it.",
    expected: "Open Investigation → Challenge passes → Pending human approval",
  },
};





function readable(

  value: string | null | undefined,

): string {

  if (!value) {

    return "—";

  }



  return value

    .replaceAll("_", " ")

    .replace(

      /\b\w/g,

      (letter: string) =>

        letter.toUpperCase(),

    );

}





function percent(

  value: number | null,

): string {

  if (value === null) {

    return "—";

  }



  return `${Math.round(value * 100)}%`;

}





function evaluationMetricLabel(

  name: string,

): string {

  const labels: Record<string, string> = {

    invalid_citation_block_rate:
      "Invalid Citation Blocking",

    challenged_action_block_rate:
      "Challenge Enforcement",

    approval_gate_rate:
      "Human Approval Gating",

    read_only_execution_rate:
      "Read-only Execution",

  };

  return labels[name] ?? readable(name);
}



function replayImpactSummary(

  result: PolicyReplayResult,

): string {

  if (!result.outcome_changed) {

    return `${result.case_id} keeps the same outcome under both policy versions.`;

  }

  if (result.change_type === "newly_blocked") {

    return `${result.case_id} changes from allowed to blocked under the candidate policy.`;

  }

  if (result.change_type === "newly_allowed") {

    return `${result.case_id} changes from blocked to allowed under the candidate policy.`;

  }

  return `${result.case_id} changes outcome under the candidate policy.`;
}



function StatusBadge({

  value,

}: {

  value: string;

}) {

  const normalized =

    value.toLowerCase();



  let kind = "neutral";



  if (

    [

      "approved",

      "pass",

      "active",

      "allowed",

      "paid",

    ].includes(normalized)

  ) {

    kind = "success";

  }



  if (

    [

      "challenge",

      "challenged",

      "blocked",

      "rejected",

      "missing",

      "newly blocked",

      "newly_blocked",

    ].includes(normalized)

  ) {

    kind = "danger";

  }



  if (

    [

      "pending",

      "held",

      "human review",

    ].includes(normalized)

  ) {

    kind = "warning";

  }



  return (

    <span

      className={`badge badge-${kind}`}

    >

      {readable(value)}

    </span>

  );

}





function Section({

  title,

  children,

  className = "",

}: {

  title: string;

  children: ReactNode;

  className?: string;

}) {

  return (

    <section

      className={`panel ${className}`}

    >

      <div className="panel-title">

        {title}

      </div>



      {children}

    </section>

  );

}





function EmptyState({

  children,

}: {

  children: ReactNode;

}) {

  return (

    <div className="empty-state">

      {children}

    </div>

  );

}





function CasesView() {

  const [

    cases,

    setCases,

  ] = useState<CaseSummary[]>([]);



  const [

    selectedCaseId,

    setSelectedCaseId,

  ] = useState("");



  const [

    context,

    setContext,

  ] = useState<CaseContext | null>(

    null,

  );



  const [

    analysis,

    setAnalysis,

  ] = useState<CaseAnalysis | null>(

    null,

  );



  const [

    requestText,

    setRequestText,

  ] = useState(

    "My housing assistance payment has not arrived. Can you check what happened?",

  );



  const [

    search,

    setSearch,

  ] = useState("");



  const [

    busy,

    setBusy,

  ] = useState(false);



  const [

    error,

    setError,

  ] = useState<string | null>(

    null,

  );





  async function loadCases() {

    try {

      const result =

        await api.listCases();



      const demoCases =
        result.filter(
          (item) =>
            !item.case_id.startsWith(
              "CF-EVAL-",
            ),
        );



      setCases(

        demoCases,

      );



      if (

        !selectedCaseId &&

        demoCases.length > 0

      ) {

        const preferred =

          demoCases.find(

            (item) =>

              item.case_id ===

              "CF-10001",

          );



        setSelectedCaseId(

          preferred?.case_id ??

            demoCases[0].case_id,

        );

      }

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Unable to load cases.",

      );

    }

  }





  async function loadContext(

    caseId: string,

  ) {

    if (!caseId) {

      return;

    }



    try {

      setError(

        null,

      );



      const result =

        await api.getCase(

          caseId,

        );



      setContext(

        result,

      );

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Unable to load case.",

      );

    }

  }





  useEffect(() => {

    void loadCases();

  }, []);





  useEffect(() => {

    if (selectedCaseId) {

      setAnalysis(

        null,

      );



      void loadContext(

        selectedCaseId,

      );

    }

  }, [selectedCaseId]);





  const filteredCases =

    useMemo(

      () => {

        const term =

          search

            .trim()

            .toLowerCase();



        if (!term) {

          return cases;

        }



        return cases.filter(
          (item) => {
            const scenario =
              DEMO_SCENARIOS[item.case_id];

            return (
              item.case_id.toLowerCase().includes(term) ||
              item.program.toLowerCase().includes(term) ||
              item.status.toLowerCase().includes(term) ||
              scenario?.title.toLowerCase().includes(term) ||
              scenario?.sidebarDescription
                .toLowerCase()
                .includes(term)
            );
          },
        );

      },

      [

        cases,

        search,

      ],

    );





  async function submitRequest(

    event: FormEvent,

  ) {

    event.preventDefault();



    if (

      !selectedCaseId ||

      !requestText.trim()

    ) {

      return;

    }



    try {

      setBusy(

        true,

      );



      setError(

        null,

      );



      setAnalysis(

        null,

      );



      const request =

        await api.createRequest(

          selectedCaseId,

          requestText.trim(),

        );



      const result =

        await api.analyze(

          selectedCaseId,

          request.event_id,

        );



      setAnalysis(

        result,

      );



      await loadContext(

        selectedCaseId,

      );

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Analysis failed.",

      );

    } finally {

      setBusy(

        false,

      );

    }

  }





  const selectedScenario =
    DEMO_SCENARIOS[selectedCaseId];


  return (

    <div className="cases-layout">

      <aside className="case-list-panel">

        <div className="case-list-header">

          <div>

            <div className="eyebrow">

              CASE DIRECTORY

            </div>



            <h2>

              Cases

            </h2>

          </div>



          <span className="count-pill">

            {cases.length}

          </span>

        </div>



        <input

          className="input"

          placeholder="Search cases..."

          value={search}

          onChange={(event) =>

            setSearch(

              event.target.value,

            )

          }

        />



        <div className="case-list">

          {filteredCases.map(

            (item) => (

              <button

                key={

                  item.case_id

                }

                className={

                  selectedCaseId ===

                  item.case_id

                    ? "case-list-item active"

                    : "case-list-item"

                }

                onClick={() =>

                  setSelectedCaseId(

                    item.case_id,

                  )

                }

              >

                <div className="case-list-top">

                  <strong>

                    {item.case_id}

                  </strong>



                  <StatusBadge

                    value={

                      item.status

                    }

                  />

                </div>



                <span className="case-demo-label">
                  {DEMO_SCENARIOS[item.case_id]?.title ??
                    readable(item.program)}
                </span>

                {DEMO_SCENARIOS[item.case_id] && (
                  <span className="case-demo-description">
                    {DEMO_SCENARIOS[item.case_id].sidebarDescription}
                  </span>
                )}

              </button>

            ),

          )}

        </div>

      </aside>



      <main className="case-content">

        {error && (

          <div className="alert alert-error">

            {error}

          </div>

        )}



        {!context ? (

          <EmptyState>

            Select a case to begin.

          </EmptyState>

        ) : (

          <>

            <div className="page-heading">

              <div>

                <div className="eyebrow">

                  CASE

                </div>



                <h1>

                  {

                    context.case

                      .case_id

                  }

                </h1>



                <p>

                  {readable(

                    context.case

                      .program,

                  )}

                  {" · "}

                  {

                    context.citizen

                      .full_name

                  }

                </p>

              </div>



              <StatusBadge

                value={

                  context.case.status

                }

              />

            </div>



            <div className="detail-grid">

              <Section title="Citizen">

                <dl className="details">

                  <div>

                    <dt>

                      Name

                    </dt>



                    <dd>

                      {

                        context.citizen

                          .full_name

                      }

                    </dd>

                  </div>



                  <div>

                    <dt>

                      Email

                    </dt>



                    <dd>

                      {

                        context.citizen

                          .email ?? "—"

                      }

                    </dd>

                  </div>



                  <div>

                    <dt>

                      Phone

                    </dt>



                    <dd>

                      {

                        context.citizen

                          .phone ?? "—"

                      }

                    </dd>

                  </div>

                </dl>

              </Section>



              <Section title="Payments">

                {context.payments

                  .length === 0 ? (

                  <EmptyState>

                    No payments.

                  </EmptyState>

                ) : (

                  context.payments.map(

                    (payment) => (

                      <div

                        className="record-row"

                        key={

                          payment.payment_id

                        }

                      >

                        <div>

                          <strong>

                            $

                            {

                              payment.amount

                            }

                          </strong>



                          <span>

                            {

                              payment.scheduled_date

                            }

                          </span>

                        </div>



                        <StatusBadge

                          value={

                            payment.status

                          }

                        />

                      </div>

                    ),

                  )

                )}

              </Section>



              <Section title="Documents">

                {context.documents

                  .length === 0 ? (

                  <EmptyState>

                    No documents.

                  </EmptyState>

                ) : (

                  context.documents.map(

                    (document) => (

                      <div

                        className="record-row"

                        key={

                          document.document_id

                        }

                      >

                        <div>

                          <strong>

                            {readable(

                              document.document_type,

                            )}

                          </strong>



                          <span>

                            {

                              document.file_name

                            }

                          </span>

                        </div>



                        <StatusBadge

                          value={

                            document.review_status

                          }

                        />

                      </div>

                    ),

                  )

                )}

              </Section>



              <Section title="Existing Approvals">

                {context.approvals

                  .length === 0 ? (

                  <EmptyState>

                    No approvals for this case.

                  </EmptyState>

                ) : (

                  context.approvals.map(

                    (approval) => (

                      <div

                        className="record-row"

                        key={

                          approval.approval_id

                        }

                      >

                        <div>

                          <strong>

                            {readable(

                              approval.action_type,

                            )}

                          </strong>



                          <span>

                            {

                              approval.approval_id

                            }

                          </span>

                        </div>



                        <StatusBadge

                          value={

                            approval.status

                          }

                        />

                      </div>

                    ),

                  )

                )}

              </Section>

            </div>



            {selectedScenario && (
              <section className="demo-guide">
                <div className="demo-guide-copy">
                  <div className="eyebrow">
                    RECRUITER DEMO GUIDE
                  </div>

                  <div className="demo-guide-title-row">
                    <h3>{selectedScenario.title}</h3>
                    <span className="demo-case-id">
                      {selectedCaseId}
                    </span>
                  </div>

                  <p className="demo-guide-description">
                    {selectedScenario.description}
                  </p>

                  <div className="demo-expected-path">
                    <span>Expected path</span>
                    <strong>{selectedScenario.expected}</strong>
                  </div>
                </div>

                <button
                  className="button button-secondary demo-prompt-button"
                  type="button"
                  onClick={() =>
                    setRequestText(selectedScenario.prompt)
                  }
                >
                  Use suggested request
                </button>
              </section>
            )}

            <Section

              title="New Citizen Request"

              className="request-panel"

            >

              <form

                onSubmit={

                  submitRequest

                }

              >

                <textarea

                  className="textarea"

                  value={

                    requestText

                  }

                  onChange={(

                    event,

                  ) =>

                    setRequestText(

                      event.target

                        .value,

                    )

                  }

                  rows={4}

                />



                <div className="form-footer">

                  <span className="form-hint">

                    CivicFlow will create

                    the request, retrieve

                    policy, analyze it,

                    and apply its safety

                    gates.

                  </span>



                  <button

                    className="button button-primary"

                    type="submit"

                    disabled={busy}

                  >

                    {busy

                      ? "Running CivicFlow..."

                      : "Create + Analyze"}

                  </button>

                </div>

              </form>

            </Section>



            {analysis && (

              <AnalysisView

                analysis={

                  analysis

                }

              />

            )}

          </>

        )}

      </main>

    </div>

  );

}





function AnalysisView({

  analysis,

}: {

  analysis: CaseAnalysis;

}) {

  const displayedAction =

    analysis.challenged_action ??

    analysis.recommended_action;



  return (

    <div className="analysis-section">

      <div className="section-heading">

        <div>

          <div className="eyebrow">

            CIVICFLOW ANALYSIS

          </div>



          <h2>

            Decision Trace

          </h2>

        </div>



        {analysis.requires_human_review ? (

          <StatusBadge

            value="human review"

          />

        ) : (

          <StatusBadge

            value="pass"

          />

        )}

      </div>



      <div className="analysis-grid">

        <Section title="Classification">

          <div className="large-value">

            {readable(

              analysis.request_type,

            )}

          </div>



          <div className="metric-line">

            <span>

              Confidence

            </span>



            <strong>

              {percent(

                analysis.classification_confidence,

              )}

            </strong>

          </div>



          <div className="metric-line">

            <span>

              Source

            </span>



            <strong>

              {readable(

                analysis.classification_source,

              )}

            </strong>

          </div>

        </Section>



        <Section title="Proposed Action">

          <div className="large-value">

            {displayedAction

              ? readable(

                  displayedAction,

                )

              : "No automated action"}

          </div>



          <p className="muted">

            {

              analysis.recommendation_rationale ??

              "No recommendation rationale available."

            }

          </p>



          {analysis.recommendation_confidence !==

            null && (

            <div className="metric-line">

              <span>

                Recommendation confidence

              </span>



              <strong>

                {percent(

                  analysis.recommendation_confidence,

                )}

              </strong>

            </div>

          )}

        </Section>



        <Section title="Deterministic Policy Gate">

          <div className="status-line">

            {analysis.policy_check_allowed ===

            true ? (

              <StatusBadge

                value="allowed"

              />

            ) : analysis.policy_check_allowed ===

              false ? (

              <StatusBadge

                value="blocked"

              />

            ) : (

              <StatusBadge

                value="not evaluated"

              />

            )}

          </div>



          <ul className="reason-list">

            {analysis.policy_check_reasons.map(

              (

                reason,

                index,

              ) => (

                <li key={index}>

                  {reason}

                </li>

              ),

            )}

          </ul>

        </Section>



        <Section title="Tool Gate">

          <div className="metric-line">

            <span>

              Access

            </span>



            <strong>

              {readable(

                analysis.tool_access_mode,

              )}

            </strong>

          </div>



          <div className="metric-line">

            <span>

              Human approval

            </span>



            <strong>

              {analysis.tool_requires_approval ===

              null

                ? "—"

                : analysis.tool_requires_approval

                  ? "Required"

                  : "Not required"}

            </strong>

          </div>



          <div className="metric-line">

            <span>

              Executed tool

            </span>



            <strong>

              {readable(

                analysis.executed_tool,

              )}

            </strong>

          </div>

        </Section>

      </div>



      <Section

        title="Policy Evidence"

        className="policy-panel"

      >

        {analysis.policy_evidence

          .length === 0 ? (

          <EmptyState>

            No policy evidence

            retrieved.

          </EmptyState>

        ) : (

          <div className="policy-list">

            {analysis.policy_evidence.map(

              (evidence) => (

                <article

                  className="policy-card"

                  key={

                    evidence.chunk_id

                  }

                >

                  <div className="policy-card-heading">

                    <div>

                      <strong>

                        {

                          evidence.policy_id

                        }

                        {" · v"}

                        {

                          evidence.version

                        }

                      </strong>



                      <span>

                        {

                          evidence.section

                        }

                      </span>

                    </div>



                    <span className="similarity">

                      {Math.round(

                        evidence.similarity *

                          100,

                      )}

                      % match

                    </span>

                  </div>



                  <p>

                    {

                      evidence.content

                    }

                  </p>



                  <code>

                    {

                      evidence.chunk_id

                    }

                  </code>

                </article>

              ),

            )}

          </div>

        )}

      </Section>



      <Section

        title="Decision Challenge"

        className={

          analysis.challenge_verdict ===

          "challenge"

            ? "challenge-panel danger-panel"

            : analysis.challenge_verdict ===

                "pass"

              ? "challenge-panel success-panel"

              : "challenge-panel"

        }

      >

        {analysis.challenge_verdict ? (

          <>

            <div className="challenge-header">

              <StatusBadge

                value={

                  analysis.challenge_verdict

                }

              />



              <span>

                Confidence{" "}

                {percent(

                  analysis.challenge_confidence,

                )}

              </span>

            </div>



            <ul className="reason-list">

              {analysis.challenge_reasons.map(

                (

                  reason,

                  index,

                ) => (

                  <li key={index}>

                    {reason}

                  </li>

                ),

              )}

            </ul>



            {analysis

              .challenge_missing_evidence

              .length > 0 && (

              <div className="missing-evidence">

                <strong>

                  Missing evidence

                </strong>



                {analysis.challenge_missing_evidence.map(

                  (

                    item,

                    index,

                  ) => (

                    <div key={index}>

                      {item}

                    </div>

                  ),

                )}

              </div>

            )}

          </>

        ) : (

          <p className="muted">

            Decision Challenge was

            not required. Read-only

            actions can bypass the

            consequential-action

            challenge gate.

          </p>

        )}

      </Section>



      {analysis.approval_request && (

        <Section title="Human Approval">

          <div className="approval-highlight">

            <div>

              <div className="eyebrow">

                PENDING APPROVAL

              </div>



              <strong>

                {readable(

                  analysis.approval_request

                    .action_type,

                )}

              </strong>



              <span>

                {

                  analysis.approval_request

                    .approval_id

                }

              </span>

            </div>



            <StatusBadge

              value={

                analysis.approval_request

                  .status

              }

            />

          </div>

        </Section>

      )}

    </div>

  );

}





function ApprovalsView() {

  const [

    approvals,

    setApprovals,

  ] = useState<Approval[]>([]);



  const [

    status,

    setStatus,

  ] = useState("pending");



  const [

    caseFilter,

    setCaseFilter,

  ] = useState("");



  const [

    reviewer,

    setReviewer,

  ] = useState("YK");



  const [

    busyId,

    setBusyId,

  ] = useState<string | null>(

    null,

  );



  const [

    error,

    setError,

  ] = useState<string | null>(

    null,

  );





  async function load() {

    try {

      setError(

        null,

      );



      const result =

        await api.listApprovals(

          status || undefined,

          caseFilter.trim() ||

            undefined,

        );



      setApprovals(

        result.filter(
          (approval) =>
            !approval.case_id.startsWith(
              "CF-EVAL-",
            ),
        ),

      );

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Unable to load approvals.",

      );

    }

  }





  useEffect(() => {

    void load();

  }, []);





  async function decide(

    approvalId: string,

    decision: "approve" | "reject",

  ) {

    if (!reviewer.trim()) {

      setError(

        "Enter a reviewer name.",

      );



      return;

    }



    try {

      setBusyId(

        approvalId,

      );



      setError(

        null,

      );



      if (

        decision ===

        "approve"

      ) {

        await api.approve(

          approvalId,

          reviewer.trim(),

        );

      } else {

        await api.reject(

          approvalId,

          reviewer.trim(),

        );

      }



      await load();

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Decision failed.",

      );

    } finally {

      setBusyId(

        null,

      );

    }

  }





  return (

    <div className="standard-page">

      <div className="page-heading">

        <div>

          <div className="eyebrow">

            HUMAN-IN-THE-LOOP

          </div>



          <h1>

            Approvals

          </h1>



          <p>

            Review consequential

            actions before any

            state-changing tool can

            execute.

          </p>

        </div>

      </div>



      <Section title="Filters">

        <div className="filter-row">

          <label>

            <span>

              Status

            </span>



            <select

              className="input"

              value={status}

              onChange={(event) =>

                setStatus(

                  event.target.value,

                )

              }

            >

              <option value="pending">

                Pending

              </option>



              <option value="approved">

                Approved

              </option>



              <option value="rejected">

                Rejected

              </option>



              <option value="">

                All

              </option>

            </select>

          </label>



          <label>

            <span>

              Case ID

            </span>



            <input

              className="input"

              value={caseFilter}

              placeholder="Optional"

              onChange={(event) =>

                setCaseFilter(

                  event.target.value,

                )

              }

            />

          </label>



          <label>

            <span>

              Reviewer

            </span>



            <input

              className="input"

              value={reviewer}

              onChange={(event) =>

                setReviewer(

                  event.target.value,

                )

              }

            />

          </label>



          <button

            className="button button-secondary"

            onClick={() =>

              void load()

            }

          >

            Refresh

          </button>

        </div>

      </Section>



      {error && (

        <div className="alert alert-error">

          {error}

        </div>

      )}



      <Section

        title={`${approvals.length} Approvals`}

      >

        {approvals.length ===

        0 ? (

          <EmptyState>

            No approvals match

            these filters.

          </EmptyState>

        ) : (

          <div className="approval-list">

            {approvals.map(

              (approval) => (

                <article

                  className="approval-card"

                  key={

                    approval.approval_id

                  }

                >

                  <div>

                    <div className="approval-title">

                      <strong>

                        {readable(

                          approval.action_type,

                        )}

                      </strong>



                      <StatusBadge

                        value={

                          approval.status

                        }

                      />

                    </div>



                    <div className="approval-meta">

                      <span>

                        {

                          approval.case_id

                        }

                      </span>



                      <span>

                        {

                          approval.approval_id

                        }

                      </span>



                      {approval.reviewer && (

                        <span>

                          Reviewer:{" "}

                          {

                            approval.reviewer

                          }

                        </span>

                      )}

                    </div>

                  </div>



                  {approval.status ===

                    "pending" && (

                    <div className="approval-actions">

                      <button

                        className="button button-danger-outline"

                        disabled={

                          busyId ===

                          approval.approval_id

                        }

                        onClick={() =>

                          void decide(

                            approval.approval_id,

                            "reject",

                          )

                        }

                      >

                        Reject

                      </button>



                      <button

                        className="button button-primary"

                        disabled={

                          busyId ===

                          approval.approval_id

                        }

                        onClick={() =>

                          void decide(

                            approval.approval_id,

                            "approve",

                          )

                        }

                      >

                        Approve

                      </button>

                    </div>

                  )}

                </article>

              ),

            )}

          </div>

        )}

      </Section>

    </div>

  );

}





function PolicyReplayView() {

  const [

    action,

    setAction,

  ] = useState(

    "open_investigation",

  );



  const [

    caseId,

    setCaseId,

  ] = useState(

    "CF-10001",

  );



  const [

    baseline,

    setBaseline,

  ] = useState(1);



  const [

    candidate,

    setCandidate,

  ] = useState(2);



  const [

    singleResult,

    setSingleResult,

  ] = useState<PolicyReplayResult | null>(

    null,

  );



  const [

    batchResult,

    setBatchResult,

  ] = useState<PolicyReplayBatchResult | null>(

    null,

  );



  const [

    busy,

    setBusy,

  ] = useState(false);



  const [

    error,

    setError,

  ] = useState<string | null>(

    null,

  );



  function loadReplayDemo() {

    setAction(
      "open_investigation",
    );

    setCaseId(
      "CF-10001",
    );

    setBaseline(1);

    setCandidate(2);

    setSingleResult(
      null,
    );

    setBatchResult(
      null,
    );

    setError(
      null,
    );
  }



  async function runSingle() {

    try {

      setBusy(

        true,

      );



      setError(

        null,

      );



      setBatchResult(

        null,

      );



      const result =

        await api.replayCase(

          caseId.trim(),

          action,

          baseline,

          candidate,

        );



      setSingleResult(

        result,

      );

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Replay failed.",

      );

    } finally {

      setBusy(

        false,

      );

    }

  }





  async function runBatch() {

    try {

      setBusy(

        true,

      );



      setError(

        null,

      );



      setSingleResult(

        null,

      );



      const result =

        await api.replayBatch(

          action,

          baseline,

          candidate,

        );



      setBatchResult(

        result,

      );

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Replay failed.",

      );

    } finally {

      setBusy(

        false,

      );

    }

  }



  const changedRate =
    batchResult &&
    batchResult.total_cases > 0
      ? Math.round(
          (
            batchResult.changed_cases /
            batchResult.total_cases
          ) * 100,
        )
      : 0;



  return (

    <div className="standard-page">

      <div className="page-heading">

        <div>

          <div className="eyebrow">

            POLICY IMPACT

          </div>



          <h1>

            Policy Replay

          </h1>



          <p>

            Compare the same case facts

            under different policy versions

            without rerunning the LLM.

          </p>

        </div>



        <span className="feature-badge">
          Deterministic · No LLM
        </span>

      </div>



      <section className="feature-intro">

        <div className="feature-intro-copy">

          <div className="eyebrow">
            RECRUITER DEMO
          </div>

          <h2>
            See how a policy change alters a case decision
          </h2>

          <p>
            HA-PAY v2 adds an approved address-verification
            requirement for opening a payment investigation.
            Replay keeps the case facts fixed so any changed
            outcome is attributable to policy, not model drift.
          </p>

          <div className="replay-story-flow">
            <span>HA-PAY v1</span>
            <strong>same case facts</strong>
            <span>HA-PAY v2</span>
          </div>

        </div>



        <button
          className="button button-secondary"
          type="button"
          onClick={loadReplayDemo}
        >
          Load recruiter demo
        </button>

      </section>



      <Section title="Replay Configuration">

        <div className="replay-controls">

          <label>

            <span>

              Action

            </span>



            <select

              className="input"

              value={action}

              onChange={(event) =>

                setAction(

                  event.target.value,

                )

              }

            >

              <option value="open_investigation">

                Open Investigation

              </option>



              <option value="check_payment">

                Check Payment

              </option>

            </select>

          </label>



          <label>

            <span>

              Baseline

            </span>



            <select

              className="input"

              value={baseline}

              onChange={(event) =>

                setBaseline(

                  Number(

                    event.target.value,

                  ),

                )

              }

            >

              <option value={1}>

                HA-PAY v1

              </option>



              <option value={2}>

                HA-PAY v2

              </option>

            </select>

          </label>



          <div className="replay-arrow">

            →

          </div>



          <label>

            <span>

              Candidate

            </span>



            <select

              className="input"

              value={candidate}

              onChange={(event) =>

                setCandidate(

                  Number(

                    event.target.value,

                  ),

                )

              }

            >

              <option value={1}>

                HA-PAY v1

              </option>



              <option value={2}>

                HA-PAY v2

              </option>

            </select>

          </label>



          <label>

            <span>

              Case ID

            </span>



            <input

              className="input"

              value={caseId}

              onChange={(event) =>

                setCaseId(

                  event.target.value,

                )

              }

            />

          </label>

        </div>



        <div className="button-row">

          <button

            className="button button-secondary"

            disabled={

              busy ||

              !caseId.trim()

            }

            onClick={() =>

              void runSingle()

            }

          >

            {busy
              ? "Running..."
              : "Replay One Case"}

          </button>



          <button

            className="button button-primary"

            disabled={busy}

            onClick={() =>

              void runBatch()

            }

          >

            {busy
              ? "Running..."
              : "Replay All Stored Cases"}

          </button>

        </div>

      </Section>



      {error && (

        <div className="alert alert-error">

          {error}

        </div>

      )}



      {singleResult && (

        <>

          <div
            className={
              singleResult.outcome_changed
                ? "replay-impact-banner changed"
                : "replay-impact-banner"
            }
          >
            <div>
              <span>Replay conclusion</span>
              <strong>
                {replayImpactSummary(
                  singleResult,
                )}
              </strong>
            </div>

            <StatusBadge
              value={
                singleResult.outcome_changed
                  ? singleResult.change_type
                  : "unchanged"
              }
            />
          </div>



          <Section title="Case Replay Result">

            <div className="replay-comparison">

              <OutcomeCard

                title={`HA-PAY v${singleResult.baseline.version}`}

                outcome={

                  singleResult.baseline

                }

              />



              <div className="comparison-arrow">

                →

              </div>



              <OutcomeCard

                title={`HA-PAY v${singleResult.candidate.version}`}

                outcome={

                  singleResult.candidate

                }

              />

            </div>



            <div className="replay-result-footer">

              <span>
                Same facts · Different policy
              </span>



              <strong>

                {

                  singleResult.case_id

                }

              </strong>

            </div>

          </Section>

        </>

      )}



      {batchResult && (

        <>

          <div className="summary-grid replay-summary-grid">

            <div className="summary-card">

              <span>

                Cases replayed

              </span>



              <strong>

                {

                  batchResult.total_cases

                }

              </strong>

            </div>



            <div className="summary-card">

              <span>

                Changed

              </span>



              <strong>

                {

                  batchResult.changed_cases

                }

              </strong>

            </div>



            <div className="summary-card">

              <span>

                Unchanged

              </span>



              <strong>

                {

                  batchResult.unchanged_cases

                }

              </strong>

            </div>



            <div className="summary-card summary-card-accent">

              <span>
                Outcome change rate
              </span>

              <strong>
                {changedRate}%
              </strong>

            </div>

          </div>



          <div className="batch-insight">
            <strong>
              {batchResult.changed_cases} of {batchResult.total_cases} stored cases
            </strong>
            <span>
              produce a different decision under the candidate policy.
            </span>
          </div>



          <Section title="Replay Results">

            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>

                    <th>

                      Case

                    </th>



                    <th>

                      Baseline

                    </th>



                    <th>

                      Candidate

                    </th>



                    <th>

                      Impact

                    </th>

                  </tr>

                </thead>



                <tbody>

                  {batchResult.results.map(

                    (result) => (

                      <tr

                        key={

                          result.case_id

                        }

                      >

                        <td>

                          <strong>

                            {

                              result.case_id

                            }

                          </strong>

                        </td>



                        <td>

                          <StatusBadge

                            value={

                              result.baseline

                                .allowed

                                ? "allowed"

                                : "blocked"

                            }

                          />

                        </td>



                        <td>

                          <StatusBadge

                            value={

                              result.candidate

                                .allowed

                                ? "allowed"

                                : "blocked"

                            }

                          />

                        </td>



                        <td>

                          <StatusBadge

                            value={

                              result.change_type

                            }

                          />

                        </td>

                      </tr>

                    ),

                  )}

                </tbody>

              </table>

            </div>

          </Section>

        </>

      )}

    </div>

  );

}



function OutcomeCard({

  title,

  outcome,

}: {

  title: string;



  outcome: {

    allowed: boolean;

    requires_human_review: boolean;

    reasons: string[];

  };

}) {

  return (

    <div className="outcome-card">

      <div className="outcome-heading">

        <strong>

          {title}

        </strong>



        <StatusBadge

          value={

            outcome.allowed

              ? "allowed"

              : "blocked"

          }

        />

      </div>



      <ul className="reason-list">

        {outcome.reasons.map(

          (

            reason,

            index,

          ) => (

            <li key={index}>

              {reason}

            </li>

          ),

        )}

      </ul>

    </div>

  );

}





function EvaluationView() {

  const [

    report,

    setReport,

  ] = useState<EvaluationReport | null>(

    null,

  );



  const [

    busy,

    setBusy,

  ] = useState(false);



  const [

    error,

    setError,

  ] = useState<string | null>(

    null,

  );





  async function run() {

    try {

      setBusy(

        true,

      );



      setError(

        null,

      );



      const result =

        await api.evaluation();



      setReport(

        result,

      );

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Evaluation failed.",

      );

    } finally {

      setBusy(

        false,

      );

    }

  }





  useEffect(() => {

    void run();

  }, []);



  const totalChecks =
    report
      ? report.metrics.reduce(
          (sum, metric) =>
            sum + metric.total,
          0,
        )
      : 0;



  const passedChecks =
    report
      ? report.metrics.reduce(
          (sum, metric) =>
            sum + metric.passed,
          0,
        )
      : 0;



  const allControlsPassed =
    Boolean(report) &&
    report!.metrics.length > 0 &&
    report!.metrics.every(
      (metric) =>
        metric.passed === metric.total,
    );



  return (

    <div className="standard-page">

      <div className="page-heading">

        <div>

          <div className="eyebrow">

            SYSTEM EVALUATION

          </div>



          <h1>

            Evaluation

          </h1>



          <p>

            Validate CivicFlow's deterministic

            safety and workflow controls across

            designed synthetic scenarios.

          </p>

        </div>



        <button

          className="button button-primary"

          disabled={busy}

          onClick={() =>

            void run()

          }

        >

          {busy

            ? "Running..."

            : report
              ? "Re-run Evaluation"
              : "Run Evaluation"}

        </button>

      </div>



      <section className="feature-intro evaluation-intro">

        <div className="feature-intro-copy">

          <div className="eyebrow">
            WHAT THIS MEASURES
          </div>

          <h2>
            Safety controls, not model accuracy
          </h2>

          <p>
            This suite uses deterministic providers and synthetic
            cases to verify that invalid citations are blocked,
            challenged actions stop, consequential actions require
            approval, and read-only actions execute safely.
          </p>

        </div>



        <span className="feature-badge">
          Synthetic · Deterministic
        </span>

      </section>



      {error && (

        <div className="alert alert-error">

          {error}

        </div>

      )}



      {!report ? (

        <Section title="Evaluation">

          <EmptyState>

            {busy

              ? "Running deterministic evaluation..."

              : "No evaluation report loaded."}

          </EmptyState>

        </Section>

      ) : (

        <>

          <div
            className={
              allControlsPassed
                ? "evaluation-verdict success"
                : "evaluation-verdict"
            }
          >
            <div>
              <span>Control-suite result</span>
              <strong>
                {allControlsPassed
                  ? "All configured controls passed their designed scenarios"
                  : "Evaluation completed with control failures to review"}
              </strong>
            </div>

            <div className="evaluation-verdict-score">
              {passedChecks}/{totalChecks}
            </div>
          </div>



          <div className="summary-grid evaluation-summary-grid">

            <div className="summary-card">

              <span>

                Synthetic Cases

              </span>



              <strong>

                {

                  report.dataset_cases

                }

              </strong>

            </div>



            <div className="summary-card">

              <span>

                Policy Replay Changes

              </span>



              <strong>

                {

                  report.replay_changed_cases

                }

              </strong>

            </div>



            <div className="summary-card">

              <span>

                Replay Unchanged

              </span>



              <strong>

                {

                  report.replay_unchanged_cases

                }

              </strong>

            </div>



            <div className="summary-card summary-card-accent">

              <span>
                Control checks passed
              </span>

              <strong>
                {passedChecks}/{totalChecks}
              </strong>

            </div>

          </div>



          <Section title="Safety & Workflow Metrics">

            <div className="metrics-grid">

              {report.metrics.map(

                (metric) => (

                  <article

                    className="metric-card"

                    key={

                      metric.name

                    }

                  >

                    <div className="metric-card-top">

                      <div>

                        <span>

                          {evaluationMetricLabel(

                            metric.name,

                          )}

                        </span>



                        <strong>

                          {

                            metric.rate

                          }

                          %

                        </strong>

                      </div>



                      <span>

                        {

                          metric.passed

                        }

                        /

                        {

                          metric.total

                        }

                      </span>

                    </div>



                    <div className="metric-progress">

                      <div

                        style={{

                          width: `${metric.rate}%`,

                        }}

                      />

                    </div>



                    <p>

                      {

                        metric.description

                      }

                    </p>

                  </article>

                ),

              )}

            </div>

          </Section>



          <Section title="Methodology & Scope">

            <div className="evaluation-method-grid">

              <div className="note-box">

                These percentages measure

                deterministic CivicFlow

                safety-control behavior on

                designed synthetic scenarios.

                They do not mean the LLM is

                100% accurate.

              </div>



              <div className="evaluation-method-card">
                <span>Evaluation design</span>
                <strong>
                  Controlled providers isolate policy and workflow behavior
                </strong>
                <p>
                  The suite deliberately exercises citation validation,
                  Decision Challenge, approval gating, read-only execution,
                  and policy-version replay independently of live-model variance.
                </p>
              </div>

            </div>



            <ul className="reason-list">

              {report.notes.map(

                (

                  note,

                  index,

                ) => (

                  <li key={index}>

                    {note}

                  </li>

                ),

              )}

            </ul>

          </Section>

        </>

      )}

    </div>

  );

}



export default function App() {

  const [

    activeTab,

    setActiveTab,

  ] = useState<Tab>("cases");



  const [

    online,

    setOnline,

  ] = useState<

    boolean | null

  >(null);





  useEffect(() => {

    api.health()

      .then(() =>

        setOnline(

          true,

        ),

      )

      .catch(() =>

        setOnline(

          false,

        ),

      );

  }, []);





  return (

    <div className="app-shell">

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-mark">

            CF

          </div>



          <div>

            <strong>

              CivicFlow

            </strong>



            <span>

              Policy-aware case ops

            </span>

          </div>

        </div>



        <nav>

          <button

            className={

              activeTab ===

              "cases"

                ? "nav-item active"

                : "nav-item"

            }

            onClick={() =>

              setActiveTab(

                "cases",

              )

            }

          >

            <span className="nav-symbol">

              C

            </span>



            Cases

          </button>



          <button

            className={

              activeTab ===

              "approvals"

                ? "nav-item active"

                : "nav-item"

            }

            onClick={() =>

              setActiveTab(

                "approvals",

              )

            }

          >

            <span className="nav-symbol">

              A

            </span>



            Approvals

          </button>



          <button

            className={

              activeTab ===

              "replay"

                ? "nav-item active"

                : "nav-item"

            }

            onClick={() =>

              setActiveTab(

                "replay",

              )

            }

          >

            <span className="nav-symbol">

              R

            </span>



            Policy Replay

          </button>



          <button

            className={

              activeTab ===

              "evaluation"

                ? "nav-item active"

                : "nav-item"

            }

            onClick={() =>

              setActiveTab(

                "evaluation",

              )

            }

          >

            <span className="nav-symbol">

              E

            </span>



            Evaluation

          </button>

        </nav>



        <div className="sidebar-footer">

          <span

            className={

              online

                ? "connection-dot online"

                : "connection-dot"

            }

          />



          {online === null

            ? "Checking API..."

            : online

              ? "FastAPI connected"

              : "Backend offline"}

        </div>

      </aside>



      <div className="workspace">

        <header className="topbar">

          <div>

            <span>

              CIVICFLOW

            </span>



            <strong>

              Decision Intelligence

            </strong>

          </div>



          <div className="environment-pill">

            LIVE DEMO

          </div>

        </header>



        <div className="main-area">

          {activeTab ===

            "cases" && (

            <CasesView />

          )}



          {activeTab ===

            "approvals" && (

            <ApprovalsView />

          )}



          {activeTab ===

            "replay" && (

            <PolicyReplayView />

          )}



          {activeTab ===

            "evaluation" && (

            <EvaluationView />

          )}

        </div>

      </div>

    </div>

  );

}