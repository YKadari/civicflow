CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE citizens (
    citizen_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(30),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE cases (
    case_id VARCHAR(20) PRIMARY KEY,
    citizen_id VARCHAR(20) NOT NULL,
    program VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL,
    opened_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,

    CONSTRAINT fk_case_citizen
        FOREIGN KEY (citizen_id)
        REFERENCES citizens(citizen_id)
);


CREATE TABLE payments (
    payment_id VARCHAR(30) PRIMARY KEY,
    case_id VARCHAR(20) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    scheduled_date DATE NOT NULL,
    paid_date DATE,
    status VARCHAR(30) NOT NULL,

    CONSTRAINT fk_payment_case
        FOREIGN KEY (case_id)
        REFERENCES cases(case_id)
);


CREATE TABLE documents (
    document_id VARCHAR(30) PRIMARY KEY,
    case_id VARCHAR(20) NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    review_status VARCHAR(30) NOT NULL,

    CONSTRAINT fk_document_case
        FOREIGN KEY (case_id)
        REFERENCES cases(case_id)
);


CREATE TABLE case_events (
    event_id VARCHAR(30) PRIMARY KEY,
    case_id VARCHAR(20) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_event_case
        FOREIGN KEY (case_id)
        REFERENCES cases(case_id)
);


CREATE TABLE approvals (
    approval_id VARCHAR(30) PRIMARY KEY,
    case_id VARCHAR(20) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL,
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decided_at TIMESTAMP,
    reviewer VARCHAR(100),

    CONSTRAINT fk_approval_case
        FOREIGN KEY (case_id)
        REFERENCES cases(case_id)
);


CREATE TABLE audit_logs (
    audit_id VARCHAR(30) PRIMARY KEY,
    case_id VARCHAR(20) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_case
        FOREIGN KEY (case_id)
        REFERENCES cases(case_id)
);

CREATE TABLE policy_chunks (
    chunk_id VARCHAR(100) PRIMARY KEY,
    policy_id VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL,
    section VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768) NOT NULL
);