Markdown
# YMCA Secure Summer Camp Registration Assistant

**Architected & Developed by:** Jane Nikolaichuk  
**Cybersecurity Foundation:** Per Scholas Certified Program (Cybersecurity)  
**Professional Experience:** Northern Regional Recreation Center, Recreation Fitness Assistant (Huntersville, NC)  
**Security Framework:** Anthropic 4D + Zero-Trust Architecture  
**Compliance:** COPPA, HIPAA, SOC 2 Type II

---

## Executive Summary

This is an **enterprise-grade, conversational AI assistant** that automates Summer Camp registration for the YMCA of Greater Charlotte while maintaining **zero-trust security** principles and full compliance with children's data protection regulations (COPPA, HIPAA).

The system is designed to:
- ✔️ Accept natural language from parents ("My child is 8, allergic to peanuts")
- ✔️ Enforce rigid, immutable data governance (no prompt injection, no PII exposure)
- ✔️ Encrypt all children's data using AES-256-GCM (AWS KMS-backed)
- ✔️ Delegate sensitive operations to human staff (payments, identity verification, exceptions)
- ✔️ Log every data access for 7-year HIPAA retention + audit trails
- ✔️ Revoke access in real-time using stateless JWT tokens + Redis blacklists

---

## Key Features

### 🔒 **Module 1: Secure Parent Interaction & PII Intake**
- **Age Gate:** Detects children under 13 (triggers COPPA regulations)
- **Consent Management:** Collects timestamped parental consent before storing data
- **Encrypted PII Storage:** All sensitive data (name, DOB, address, phone) encrypted at rest (AES-256-GCM)
- **Audit Trail:** Every PII access logged to immutable DynamoDB + S3 WORM archive

### 🔍 **Module 2: Automated Slot Availability Checks**
- **SQL Injection Prevention:** Parameterized queries via SQLAlchemy ORM
- **Prompt Injection Defense:** Rigid input validation (no dynamic SQL construction)
- **Real-Time Availability:** Direct RDS queries with query performance monitoring
- **Exception Handling:** Ambiguous requests → escalate to human staff (e.g., "My kid is 6 or 7?")

### 🔑 **Module 3: Zero-Trust Session & Token Governance**
- **Stateless JWTs:** No server-side session storage (12-factor app compliant)
- **Token TTL:** Access tokens expire in 15 minutes (no "remember me")
- **Refresh Token Flow:** Use refresh tokens (24-hr TTL) for new access tokens
- **Revocation Pipeline:** Token blacklist in Redis; auto-cleanup on expiration
- **Per-Request Validation:** Every API call validates token signature + revocation status

### 🤝 **Module 4: Exception Management & Human-in-the-Loop**
- **Strategic Delegation:** AI handles routine queries; humans handle:
  - Payment approvals (never exposed to AI)
  - Identity verification (phone, email confirmation)
  - Complex grievances ("My child has never attended before, is that OK?")
  - Medical exception reviews (allergies, special needs)
- **Escalation Workflow:** Flagged requests trigger Slack alerts → staff action
- **Decision Logging:** All human decisions logged + audited

### 📊 **Module 5: Immutable Auditing & SIEM Pipeline**
- **WORM Compliance:** S3 Object Lock (Write Once, Read Many) for audit logs
- **7-Year Retention:** HIPAA-mandated data preservation
- **Real-Time SIEM:** CloudWatch → Splunk/DataDog for anomaly detection
- **Tamper Detection:** GCM authentication tags detect any data modification
<details>
 
  
  <summary> 📸 DEMO </summary>
 
  
  <br>
  <p align="center">
</details>
<img width="1467" height="825" alt="Image" src="https://github.com/user-attachments/assets/dc7667ec-e485-4d25-a9bd-73cf8cc1082c" />
<img width="1512" height="982" alt="Image" src="https://github.com/user-attachments/assets/54587fbf-9c7a-479a-99d1-18d583aa4fbd" />
<img width="1512" height="982" alt="Image" src="https://github.com/user-attachments/assets/7bac52bc-00ad-4040-a83a-b13ecc418121" />
<img width="1512" height="982" alt="Image" src="https://github.com/user-attachments/assets/79468d0d-2f5d-4537-98f3-60012439c825" />
<img width="1512" height="982" alt="Image" src="https://github.com/user-attachments/assets/0e1ed29d-439b-41d4-b458-d60f2ffb76b3" />
<img width="1512" height="982" alt="Image" src="https://github.com/user-attachments/assets/c63d0bd3-34d5-4805-85f2-311fbd6c7ed8" />
<img width="1512" height="982" alt="Image" src="https://github.com/user-attachments/assets/c86a71d6-a5cd-4f34-b45c-1b7bd4c2070a" />
<img width="1512" height="982" alt="Image" src="https://github.com/user-attachments/assets/fe5f5456-7706-4ac1-b9cc-15396b8246f2" />
<img width="1512" height="982" alt="Image" src="https://github.com/user-attachments/assets/925a1cf7-9eb6-471b-899f-5da1991b8379" />
<img width="1512" height="982" alt="Image" src="https://github.com/user-attachments/assets/af278b6c-3700-4f82-bca5-c3a3e525df91" />


 </p>
 ---

## Architecture at a Glance
```text
┌─────────────────────────────────────────────────────────────────┐
│                   PARENT (Web/Mobile)                           │
│              "My child is 8, peanut allergy"                    │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTPS (TLS 1.3)
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│               API GATEWAY (OAuth 2.0)                           │
│         ├─ Token validation (JWT signature check)               │
│         ├─ Rate limiting (100 req/min per parent)               │
│         └─ DDoS protection (AWS WAF)                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
┌──────────────────────┐  ┌──────────────────────┐
│  CLAUDE AI (Groq)    │  │  SESSION MANAGER     │
│  ├─ Age detection    │  │  ├─ JWT validation   │
│  ├─ COPPA routing    │  │  ├─ Token revocation │
│  ├─ Input validation │  │  └─ Redis blacklist  │
│  └─ Natural language │  └──────────────────────┘
│     processing       │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     ↓           ↓
┌─────┐ ┌──────────────────-┐
│ RDS │ │ ENCRYPTION MANAGER│
│     │ │ ├─ AES-256-GCM    │
│ PII │ │ ├─ AWS KMS keys   │
│ DB  │ │ └─ Key rotation   │
└─────┘ └──────────────────-┘
   │
   ↓
┌─────────────────────┐
│  AUDIT LOGGER       │
│  ├─ DynamoDB        │
│  ├─ S3 WORM archive │
│  └─ CloudTrail      │
└─────────────────────┘
Quick Start
Prerequisites
Python 3.11+
AWS Account (KMS, RDS, DynamoDB, S3)
Docker & Docker Compose
Redis 7.0+
Installation
Bash
# Clone repository
git clone [https://github.com/jane-nikolaichuk/ymca-secure-registration.git](https://github.com/jane-nikolaichuk/ymca-secure-registration.git)
cd ymca-secure-registration-assistant

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with AWS credentials, KMS key IDs, RDS endpoint

# Initialize database
python scripts/db_schema_zero_trust.sql

# Bootstrap encryption keys
python scripts/bootstrap_encryption_keys.py

# Start Docker containers (Redis, PostgreSQL, DynamoDB Local)
docker-compose up -d

# Run security tests
pytest tests/test_security_suite.py -v

# Launch interactive demo
streamlit run scripts/demo_streamlit_ui.py
Interactive Demo (Streamlit)
Bash
streamlit run scripts/demo_streamlit_ui.py
# Opens http://localhost:8501
# Test age gate, PII encryption, slot lookup, exception handling
Security Highlights
COPPA Compliance (Children Under 13)
✔️ Age gate detects children <13
✔️ Mandatory parental consent collection
✔️ Consent expires after registration
✔️ Parent deletion requests honored (72-hour SLA)
Data Encryption (AES-256-GCM)
Python
# All PII encrypted with AES-256-GCM
encrypted_name = EncryptionManager.encrypt(
    plaintext="Emma Johnson",
    associated_data="child_id:12345:field:name"
)
# Result: {ciphertext, nonce, auth_tag} stored in RDS
Zero-Trust Token Management
Python
# JWT expires in 15 minutes
access_token_exp = datetime.utcnow() + timedelta(minutes=15)

# Parent can refresh using refresh token (24-hr TTL)
new_token = SessionManager.refresh(refresh_token)

# On logout: add token to Redis revocation list
SessionManager.revoke(access_token, reason="logout")
SQL Injection Prevention
Python
# ❌ WRONG (vulnerable to SQLi)
query = f"SELECT * FROM slots WHERE age={age}"

# ✅ RIGHT (parameterized, safe)
query = "SELECT * FROM slots WHERE age = %s"
cursor.execute(query, (age,))
Documentation
ARCHITECTURE.md - Full technical blueprint (all 5 modules)
SECURITY.md - Security controls, threat model, compliance
DEPLOYMENT_GUIDE.md - Step-by-step AWS deployment
INCIDENT_RESPONSE.md - How to handle breaches
AUDIT_TRAIL_ANALYSIS.md - Reading audit logs
Testing
Bash
# Run all security tests
pytest tests/ -v

# Test encryption/decryption
pytest tests/test_encryption.py -v

# Test token validation + revocation
pytest tests/test_token_validation.py -v

# Test SQL injection prevention
pytest tests/test_sql_injection.py -v

# Test COPPA compliance
pytest tests/test_coppa_compliance.py -v

# Generate coverage report
pytest --cov=src tests/
Contact & Support
Architect: Jane Nikolaichuk
Email: evgenikanik@gmail.com
LinkedIn: linkedin.com/in/iamjanenikolaichuk
YMCA Sponsor: YMCA of Greater Charlotte
Claude Corps Fellowship: Cohort 1 (October 2026)
License
MIT License - See LICENSE file for details
Last Updated: June 2026
Version: 1.0.0 (Production Ready)
