-- ============================================================================
-- YMCA SUMMER CAMP REGISTRATION DATABASE
-- Zero-Trust Security: Row-Level Security, Encryption, Audit Trails
-- Architect: Jane Nikolaichuk
-- ============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- SCHEMAS (Isolation)
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS parents;
CREATE SCHEMA IF NOT EXISTS children;
CREATE SCHEMA IF NOT EXISTS registrations;
CREATE SCHEMA IF NOT EXISTS camp_sessions;
CREATE SCHEMA IF NOT EXISTS exceptions;
CREATE SCHEMA IF NOT EXISTS audit_logs;

-- ============================================================================
-- PARENT SCHEMA
-- ============================================================================
CREATE TABLE parents.profiles (
    parent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_hash VARCHAR(64) NOT NULL,  -- Hashed, not plaintext
    name_encrypted TEXT,              -- Stored as Hex/Text from Python Bundle
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_parent_email ON parents.profiles(email);

ALTER TABLE parents.profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Parent can only see their own profile
CREATE POLICY parent_own_profile ON parents.profiles
    FOR SELECT
    USING (parent_id = current_setting('app.current_parent_id', true)::UUID);

-- ============================================================================
-- CHILDREN SCHEMA (PII Protected)
-- ============================================================================
CREATE TABLE children.profiles (
    child_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID NOT NULL REFERENCES parents.profiles(parent_id),
    
    -- Encrypted PII (stored as JSON text bundles for AES-256-GCM context)
    full_name_encrypted TEXT NOT NULL,
    date_of_birth_encrypted TEXT NOT NULL,
    allergies_encrypted TEXT NOT NULL,
    emergency_contact_name_encrypted TEXT NOT NULL,
    emergency_contact_phone_encrypted TEXT NOT NULL,
    home_address_encrypted TEXT NOT NULL,
    
    -- Metadata (NOT encrypted)
    age_at_registration INT CHECK (age_at_registration BETWEEN 3 AND 17),
    coppa_regulated BOOLEAN DEFAULT FALSE,
    consent_obtained BOOLEAN DEFAULT FALSE,
    consent_timestamp TIMESTAMPTZ,
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    encryption_key_version INT DEFAULT 1,
    data_retention_until TIMESTAMPTZ  -- Auto-delete after camp ends + 30 days
);

CREATE INDEX idx_child_parent_id ON children.profiles(parent_id);
CREATE INDEX idx_child_age ON children.profiles(age_at_registration);
CREATE INDEX idx_child_coppa ON children.profiles(coppa_regulated);

-- RLS: Parent can only see their own children
ALTER TABLE children.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY parent_see_own_children ON children.profiles
    FOR SELECT
    USING (parent_id = current_setting('app.current_parent_id', true)::UUID);

-- RLS: Staff can only see if child is age >=13 OR has parental consent
CREATE POLICY staff_see_consented_children ON children.profiles
    FOR SELECT
    USING (age_at_registration >= 13 OR consent_obtained = TRUE);

-- ============================================================================
-- CAMP SESSIONS SCHEMA
-- ============================================================================
CREATE TABLE camp_sessions.slots (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    age_min INT CHECK (age_min >= 3),
    age_max INT CHECK (age_max <= 17),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    enrollment INT DEFAULT 0 CHECK (enrollment <= capacity),
    price DECIMAL(10, 2) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_session_age ON camp_sessions.slots(age_min, age_max);
CREATE INDEX idx_session_dates ON camp_sessions.slots(start_date, end_date);
CREATE INDEX idx_session_availability ON camp_sessions.slots(enrollment, capacity);

-- ============================================================================
-- REGISTRATIONS SCHEMA
-- ============================================================================
CREATE TABLE registrations.enrollments (
    enrollment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children.profiles(child_id),
    parent_id UUID NOT NULL REFERENCES parents.profiles(parent_id),
    session_id UUID NOT NULL REFERENCES camp_sessions.slots(session_id),
    
    -- Payment status (delegation to human approval)
    payment_status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, APPROVED, REJECTED
    payment_approved_by VARCHAR(255),              -- Staff who approved
    payment_approved_at TIMESTAMPTZ,
    
    -- Enrollment status
    status VARCHAR(50) DEFAULT 'REGISTERED',        -- REGISTERED, ATTENDED, CANCELLED
    created_at TIMESTAMPTZ DEFAULT NOW(),
    cancelled_at TIMESTAMPTZ
);

CREATE INDEX idx_enrollment_child ON registrations.enrollments(child_id);
CREATE INDEX idx_enrollment_parent ON registrations.enrollments(parent_id);
CREATE INDEX idx_enrollment_session ON registrations.enrollments(session_id);

ALTER TABLE registrations.enrollments ENABLE ROW LEVEL SECURITY;

CREATE POLICY parent_see_own_enrollments ON registrations.enrollments
    FOR SELECT
    USING (parent_id = current_setting('app.current_parent_id', true)::UUID);

-- ============================================================================
-- EXCEPTIONS SCHEMA
-- ============================================================================
CREATE TABLE exceptions.tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    parent_id_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash
    issue_type VARCHAR(100) NOT NULL,     -- ambiguity, documentation, medical, etc.
    flags JSONB NOT NULL,                 -- Array of flags
    ai_confidence DECIMAL(3, 2),
    status VARCHAR(50) DEFAULT 'PENDING_REVIEW',  -- PENDING_REVIEW, APPROVED, DENIED
    resolved_by VARCHAR(255),             -- Staff who resolved
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_exception_status ON exceptions.tickets(status);
CREATE INDEX idx_exception_created ON exceptions.tickets(created_at);

-- ============================================================================
-- AUDIT LOGS SCHEMA (Immutable, Append-Only)
-- ============================================================================
CREATE TABLE audit_logs.entries (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    parent_id_hash VARCHAR(64),
    child_id_hash VARCHAR(64),
    action VARCHAR(100) NOT NULL,         -- READ, DECRYPT, ENCRYPT, APPROVE, DENY
    status VARCHAR(50) NOT NULL,          -- SUCCESS, FAILURE, DENIED
    reason TEXT,
    ip_address_hash VARCHAR(64),
    user_agent_hash VARCHAR(64),
    session_jti VARCHAR(255),
    source_line VARCHAR(255),
    
    -- TTL (7 years for HIPAA)
    ttl TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '2555 days')
);

CREATE INDEX idx_audit_timestamp ON audit_logs.entries(timestamp DESC);
CREATE INDEX idx_audit_event_type ON audit_logs.entries(event_type);

-- Append-Only Security Trigger Enforcement
CREATE OR REPLACE FUNCTION audit_logs.prevent_loss() 
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Crypto Audit Logs are immutable. Delete/Update operations are strictly denied.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER lock_audit_trail
    BEFORE UPDATE OR DELETE ON audit_logs.entries
    FOR EACH ROW EXECUTE FUNCTION audit_logs.prevent_loss();

-- ============================================================================
-- ROLES & RBAC
-- ============================================================================
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'parent_readonly') THEN
        CREATE ROLE parent_readonly;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ymca_staff') THEN
        CREATE ROLE ymca_staff;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ymca_compliance') THEN
        CREATE ROLE ymca_compliance;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ymca_ceo_readonly') THEN
        CREATE ROLE ymca_ceo_readonly;
    END IF;
END $$;

-- Grant schema access
GRANT USAGE ON SCHEMA parents, children, registrations, camp_sessions, exceptions TO parent_readonly;
GRANT USAGE ON SCHEMA parents, children, registrations, camp_sessions, exceptions TO ymca_staff;
GRANT USAGE ON SCHEMA audit_logs TO ymca_compliance;

-- Grant table permissions
GRANT SELECT ON parents.profiles TO parent_readonly;
GRANT SELECT ON children.profiles TO parent_readonly;
GRANT SELECT ON registrations.enrollments TO parent_readonly;
GRANT SELECT ON camp_sessions.slots TO parent_readonly;
GRANT INSERT ON registrations.enrollments TO parent_readonly;

-- STAFF role
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA parents TO ymca_staff;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA children TO ymca_staff;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA registrations TO ymca_staff;
GRANT SELECT ON ALL TABLES IN SCHEMA camp_sessions TO ymca_staff;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA exceptions TO ymca_staff;

-- COMPLIANCE role (audit only)
GRANT SELECT ON audit_logs.entries TO ymca_compliance;

-- CEO role (high-level only)
GRANT SELECT ON ALL TABLES IN SCHEMA parents TO ymca_ceo_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA registrations TO ymca_ceo_readonly;

-- ============================================================================
-- SAMPLE DATA
-- ============================================================================
INSERT INTO camp_sessions.slots (name, age_min, age_max, start_date, end_date, capacity, price)
VALUES 
    ('Adventure Camp', 6, 10, '2026-07-08', '2026-07-12', 25, 299.99),
    ('STEM Camp', 8, 12, '2026-07-15', '2026-07-19', 30, 349.99),
    ('Art Camp', 4, 8, '2026-07-22', '2026-07-26', 20, 249.99)
ON CONFLICT DO NOTHING;
