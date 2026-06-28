# ARCHITECTURAL BLUEPRINT (5 MODULES)

This document provides the exhaustive, end-to-end operational workflows and structural diagrams for the YMCA Secure Registration Assistant. Built on a Zero-Trust posture and Anthropic's 4D Framework.

---

## Module 1: Secure Parent Interaction & PII Intake

### Operational Workflow
- **Discernment (Age Detection):** Claude AI parses natural language inputs to isolate minor age indicators. If the system detects a child under 13, it immediately enforces a hard COPPA routing branch.
- **Delegation (Consent Collection):** The assistant is blocked from executing downstream PII storage until the parent grants explicit, timestamped consent.
- **Diligence (Authenticated Encryption):** Plaintext PII is intercepted in memory, passed to the Encryption Manager, and encrypted using AES-256-GCM before ever hitting the persistence layer.

```text
┌─────────────────────────────────────────────────────────────┐
│  PARENT INITIATES REGISTRATION (Natural Language)           │
│  "Hi, I want to register my 8-year-old daughter Emma        │
│   for summer camp. She's allergic to peanuts."              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: CLAUDE AI - AGE DETECTION (Discernment)            │
│  ├─ Parse: "8-year-old" → child_age = 8                     │
│  ├─ Check: 8 < 13 → COPPA_REGULATED = true                  │
│  ├─ Flag: Ambiguous input? ("6 or 7?") → Ask clarification  │
│  └─ Decision: Route to COPPA consent flow                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: PARENTAL CONSENT COLLECTION (Delegation)           │
│  ├─ Bot: "Because Emma is 8, I need YOUR permission to      │
│  │        store her name, age, allergies, emergency         │
│  │        contact. OK?"                                     │
│  ├─ Parent: "Yes, I consent"                                │
│  ├─ System: Generate consent_token + timestamp              │
│  └─ Action: Add to audit log (immutable)                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: ENCRYPTION MANAGER (Diligence)                     │
│  ├─ Input: plaintext PII (Emma Johnson, DOB, etc.)          │
│  ├─ Derive: DEK from KMS master key + child_id              │
│  ├─ Encrypt: AES-256-GCM with nonce + auth_tag              │
│  ├─ Output: {ciphertext, nonce, auth_tag} → RDS             │
│  └─ Plaintext: NEVER logged, cleared from memory            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: AUDIT LOG ENTRY (Diligence)                        │
│  ├─ Event: "PII_INTAKE_COMPLETE"                            │
│  ├─ Fields: parent_id_hash, child_id_hash, timestamp,       │
│  │          consent_token, ip_hash, user_agent_hash         │
│  ├─ Storage: DynamoDB (immutable) + S3 WORM archive         │
│  └─ TTL: 2555 days (7 years, HIPAA compliance)              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
      ┌──────────────────────┐
      │  PII SECURELY STORED │
      │  (Ready for slot     │
      │   availability check)│
      └──────────────────────┘
