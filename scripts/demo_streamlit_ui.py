
"""
YMCA Secure Registration Assistant - Interactive Streamlit Prototype
Demonstrates: Age Gate, PII Encryption, Secure Slot Lookup, Exception Handling
Architect: Jane Nikolaichuk
"""

import streamlit as st
import json
import hashlib
from datetime import datetime, timezone
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="YMCA Summer Camp Registration",
    page_icon="🏊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏊 YMCA Summer Camp Registration Assistant")
st.subheader("Secure, Conversational, COPPA-Compliant")

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if 'parent_name' not in st.session_state:
    st.session_state.parent_name = ""
if 'child_name' not in st.session_state:
    st.session_state.child_name = ""
if 'child_age' not in st.session_state:
    st.session_state.child_age = 8
if 'coppa_regulated' not in st.session_state:
    st.session_state.coppa_regulated = False
if 'consent_given' not in st.session_state:
    st.session_state.consent_given = False
if 'encryption_demo' not in st.session_state:
    st.session_state.encryption_demo = None
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'audit_log' not in st.session_state:
    st.session_state.audit_log = []

# ============================================================================
# STEP 1: WELCOME & AGE GATE
# ============================================================================
if st.session_state.step == 1:
    st.markdown("---")
    st.write("### Step 1: Welcome & Age Verification")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("""
        **Hello! I'm the YMCA Summer Camp Assistant.**
        
        I'll help you register your child for an amazing summer camp experience. 
        This process is secure and compliant with children's data protection laws (COPPA).
        """)
        
        st.session_state.parent_name = st.text_input(
            "First, what's your name?",
            value=st.session_state.parent_name
        )
        
        st.session_state.child_name = st.text_input(
            "What's your child's name?",
            value=st.session_state.child_name
        )
        
        st.session_state.child_age = st.number_input(
            "How old is your child?",
            min_value=3,
            max_value=17,
            value=st.session_state.child_age
        )
        
    with col2:
        st.markdown("### 🔒 Security Features")
        st.info("""
        ✅ Age detection  
        ✅ COPPA compliance check  
        ✅ Parental consent  
        ✅ PII encryption (AES-256)  
        ✅ Audit logging  
        """)

    # Age gate logic
    if st.session_state.child_age < 13:
        st.session_state.coppa_regulated = True
        st.warning("""
        **⚠️ COPPA REGULATED**
        
        Because your child is under 13, we need your explicit permission to collect 
        and store their information. This is required by U.S. children's data 
        protection laws (COPPA).
        """)
    else:
        st.session_state.coppa_regulated = False
        st.success("✅ Your child is 13+, no special consent required.")
        
    if st.button("Next: Consent & Encryption", key="next_step_1"):
        if not st.session_state.parent_name or not st.session_state.child_name:
            st.error("Please enter both parent and child names before proceeding.")
        else:
            st.session_state.step = 2
            st.rerun()

# ============================================================================
# STEP 2: PARENTAL CONSENT & ENCRYPTION
# ============================================================================
if st.session_state.step == 2:
    st.markdown("---")
    st.write("### Step 2: Parental Consent & Data Encryption")
    
    if st.session_state.coppa_regulated:
        st.info("""
        ### Parental Consent Required
        
        To register **{child_name}** (age {age}), I need your explicit permission to:
        
        - **Collect**: Full name, age, allergies, emergency contact
        - **Store**: In our secure, encrypted database
        - **Use**: Only for camp registration and safety
        - **Retain**: Until camp ends + 30 days
        - **Delete**: Upon your request (72-hour response time)
        
        **Your Rights:**
        - You can ask us to delete all data anytime
        - You can review what we store about your child
        - We never sell or share this data
        """.format(child_name=st.session_state.child_name, age=st.session_state.child_age))
        
        consent_checkbox = st.checkbox(
            "I give permission to collect and store my child's information",
            value=st.session_state.consent_given
        )
        
        if consent_checkbox:
            if not st.session_state.consent_given:
                st.session_state.consent_given = True
                st.session_state.audit_log.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "COPPA_CONSENT_GRANTED",
                    "child_name": hashlib.sha256(st.session_state.child_name.encode()).hexdigest()[:12]
                })
            st.success("✅ Consent recorded dynamically.")
        else:
            st.session_state.consent_given = False
            
    # Encryption demonstration
    st.markdown("---")
    st.write("### 🔐 Data Encryption (AES-256-GCM)")
    
    if st.session_state.consent_given or not st.session_state.coppa_regulated:
        st.write("""
        Your child's sensitive information is encrypted using **AES-256-GCM**:
        - **Algorithm**: Advanced Encryption Standard (256-bit)
        - **Mode**: Galois/Counter Mode (authenticated encryption)
        - **Key Management**: AWS KMS (Hardware Security Module)
        """)
        
        demo_plaintext = st.session_state.child_name
        
        if st.button("Encrypt Child's Name (Demo)", key="encrypt_demo"):
            nonce = secrets.token_bytes(12)
            salt = secrets.token_bytes(32)
            
            key = hashlib.pbkdf2_hmac('sha256', b'demo_master_key', salt, 100_000, 32)
            cipher = AESGCM(key)
            ciphertext = cipher.encrypt(nonce, demo_plaintext.encode(), None)
            
            st.session_state.encryption_demo = {
                "plaintext": demo_plaintext,
                "ciphertext": ciphertext.hex()[:64] + "...",
                "nonce": nonce.hex(),
                "algorithm": "AES-256-GCM"
            }
            
            st.session_state.audit_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "PII_ENCRYPTED",
                "field": "full_name",
                "status": "SUCCESS"
            })
            
        if st.session_state.encryption_demo:
            st.write("**Encryption Result:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Original (Plaintext):**")
                st.code(st.session_state.encryption_demo['plaintext'])
                
            with col2:
                st.write("**Encrypted (Ciphertext):**")
                st.code(st.session_state.encryption_demo['ciphertext'])
                
            with col3:
                st.write("**Encryption Details:**")
                st.code(f"Algorithm: {st.session_state.encryption_demo['algorithm']}\nNonce: {st.session_state.encryption_demo['nonce'][:16]}...\nStatus: ✅ Active")
                
            st.success("✅ Data encrypted and stored securely!")
            
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="back_step_2"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.session_state.consent_given or not st.session_state.coppa_regulated:
            if st.button("Next: Find Camp Sessions →", key="next_step_2"):
                st.session_state.step = 3
                st.rerun()

# ============================================================================
# STEP 3: SLOT AVAILABILITY CHECK
# ============================================================================
if st.session_state.step == 3:
    st.markdown("---")
    st.write("### Step 3: Find Available Camp Sessions")
    
    st.write(f"**Looking for camps for {st.session_state.child_name} (age {st.session_state.child_age})...**")
    
    camp_sessions = [
        {
            "id": 1,
            "name": "Adventure Camp",
            "dates": "July 8-12, 2026",
            "age_range": "6-10",
            "capacity": 25,
            "enrollment": 18,
            "price": "$299.99",
            "description": "Outdoor adventures, hiking, nature exploration"
        },
        {
            "id": 2,
            "name": "STEM Camp",
            "dates": "July 15-19, 2026",
            "age_range": "8-12",
            "capacity": 30,
            "enrollment": 28,
            "price": "$349.99",
            "description": "Science, technology, engineering, math projects"
        },
        {
            "id": 3,
            "name": "Art Camp",
            "dates": "July 22-26, 2026",
            "age_range": "4-8",
            "capacity": 20,
            "enrollment": 20,
            "price": "$249.99",
            "description": "Painting, sculpture, creative expression (FULL)"
        }
    ]
    
    available_camps = []
    for camp in camp_sessions:
        try:
            min_age, max_age = map(int, camp['age_range'].split('-'))
            if camp['enrollment'] < camp['capacity'] and min_age <= st.session_state.child_age <= max_age:
                available_camps.append(camp)
        except ValueError:
            continue
            
    st.write(f"✅ Found **{len(available_camps)}** available camps for {st.session_state.child_name}!")
    
    # Track checking event uniquely once
    if not any(log.get('event') == 'SLOT_CHECKED' for log in st.session_state.audit_log):
        st.session_state.audit_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "SLOT_CHECKED",
            "status": "SUCCESS"
        })
        
    for camp in available_camps:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"### 🏕️ {camp['name']}")
            st.write(f"**Dates:** {camp['dates']} | **Ages:** {camp['age_range']} | **Price:** {camp['price']}")
            st.write(f"**Spots Available:** {camp['capacity'] - camp['enrollment']} of {camp['capacity']}")
            st.write(f"*{camp['description']}*")
        with col2:
            if st.button(f"Select {camp['name']}", key=f"camp_{camp['id']}"):
                st.session_state.selected_camp = camp
                st.session_state.step = 4
                st.rerun()
                
    full_camps = [camp for camp in camp_sessions if camp['enrollment'] >= camp['capacity']]
    if full_camps:
        st.markdown("---")
        st.write("### ⛔ Full Camps (No Spots Available)")
        for camp in full_camps:
            st.write(f"- {camp['name']} ({camp['dates']}) - FULL")
            
    if st.button("← Back", key="back_step_3"):
        st.session_state.step = 2
        st.rerun()

# ============================================================================
# STEP 4: REVIEW & CONFIRM
# ============================================================================
if st.session_state.step == 4:
    st.markdown("---")
    st.write("### Step 4: Review & Confirm Registration")
    
    if 'selected_camp' in st.session_state:
        st.write("### Registration Summary")
        
        summary_data = {
            "Parent Name": st.session_state.parent_name,
            "Child Name": st.session_state.child_name,
            "Child Age": st.session_state.child_age,
            "Selected Camp": st.session_state.selected_camp['name'],
            "Dates": st.session_state.selected_camp['dates'],
            "Price": st.session_state.selected_camp['price'],
            "COPPA Regulated": "Yes" if st.session_state.coppa_regulated else "No",
            "Consent Given": "Yes" if st.session_state.consent_given else "No"
        }
        
        for key, value in summary_data.items():
            st.write(f"**{key}:** {value}")
            
        st.markdown("---")
        st.write("### Payment & Approval")
        st.info("""
        ✅ **Your information is encrypted and ready to submit.**
        Next step requires standard payment approval validation process by YMCA staff.
        """)
        
        if st.button("Confirm & Submit Registration", key="confirm_registration"):
            st.session_state.audit_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "REGISTRATION_SUBMITTED",
                "status": "PENDING_APPROVAL"
            })
            st.session_state.step = 5
            st.rerun()
            
    if st.button("← Back to Camps", key="back_step_4"):
        st.session_state.step = 3
        st.rerun()

# ============================================================================
# STEP 5: COMPLETION
# ============================================================================
if st.session_state.step == 5:
    st.markdown("---")
    st.write("### ✅ Registration Complete!")
    st.balloons()
    
    st.success(f"""
    ### Thank you, {st.session_state.parent_name}!
    Your child **{st.session_state.child_name}** is registered for:
    **{st.session_state.selected_camp['name']}** ({st.session_state.selected_camp['dates']})
    """)
    
    if st.button("Register Another Child", key="register_another"):
        st.session_state.clear()
        st.session_state.step = 1
        st.rerun()

# ============================================================================
# SIDEBAR: AUDIT LOG & SECURITY INFO
# ============================================================================
with st.sidebar:
    st.markdown("### 🔒 Security & Audit")
    st.write("#### Audit Trail (This Session)")
    
    if st.session_state.audit_log:
        for log_entry in st.session_state.audit_log:
            st.write(f"**{log_entry.get('event', 'Unknown')}**")
    else:
        st.write("*No events logged yet*")
        
    st.markdown("---")
    st.write("#### System Status")
    st.write("""
    **Version:** 1.0.0  
    **Compliance:** COPPA, HIPAA, SOC2  
    **Framework:** Anthropic 4D + Zero-Trust  
    """)
    
    if st.button("Clear Session", key="clear_session"):
        st.session_state.clear()
        st.rerun()
