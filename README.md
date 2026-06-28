
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
┌─────┐ ┌──────────────────┐
│ RDS │ │ ENCRYPTION MANAGER│
│     │ │ ├─ AES-256-GCM   │
│ PII │ │ ├─ AWS KMS keys   │
│ DB  │ │ └─ Key rotation   │
└─────┘ └──────────────────┘
   │
   ↓
┌─────────────────────┐
│  AUDIT LOGGER       │
│  ├─ DynamoDB        │
│  ├─ S3 WORM archive │
│  └─ CloudTrail      │
└─────────────────────┘
