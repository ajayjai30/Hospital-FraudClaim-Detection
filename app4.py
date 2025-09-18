# streamlit_app.py
import streamlit as st
import pandas as pd
import json
import psycopg2
from psycopg2.extras import DictCursor
import xgboost as xgb
from datetime import date
from decimal import Decimal

# --- CONFIGURATION ---
PG_CONN_STRING = "postgresql://postgres:password@localhost:5432/fraud_detection"

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SecureClaim AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- SINGLE SOURCE OF TRUTH FOR MODEL FEATURES ---
# RECTIFIED: This list now exactly matches the feature names and order the trained model expects, copied from the error log.
MODEL_FEATURE_COLUMNS = [
    'InscClaimAmtReimbursed', 'DeductibleAmtPaid', 'Gender', 'Race', 'RenalDiseaseIndicator', 'State', 
    'County', 'NoOfMonths_PartACov', 'NoOfMonths_PartBCov', 'ChronicCond_Alzheimer', 'ChronicCond_Heartfailure', 
    'ChronicCond_KidneyDisease', 'ChronicCond_Cancer', 'ChronicCond_ObstrPulmonary', 'ChronicCond_Depression', 
    'ChronicCond_Diabetes', 'ChronicCond_IschemicHeart', 'ChronicCond_Osteoporasis', 
    'ChronicCond_rheumatoidarthritis', 'ChronicCond_stroke', 'IPAnnualReimbursementAmt', 'IPAnnualDeductibleAmt', 
    'OPAnnualReimbursementAmt', 'OPAnnualDeductibleAmt', 'BeneID_freq_encoded', 'Provider_freq_encoded', 
    'AttendingPhysician_freq_encoded', 'OperatingPhysician_freq_encoded', 'OtherPhysician_freq_encoded', 
    'DiagnosisGroupCode_freq_encoded'
]


# --- CACHED RESOURCES: LOAD ONCE ---
@st.cache_resource
def load_model_and_maps():
    """Loads the XGBoost model and frequency maps from disk."""
    try:
        model = xgb.Booster()
        model.load_model("xgboost_final_model.json")
    except Exception as e:
        st.error(f"Fatal Error: Could not load model. Please ensure 'xgboost_final_model.json' is in the correct directory. Details: {e}")
        return None, None

    try:
        with open('frequency_maps.txt', 'r') as f:
            freq_maps = json.load(f)
    except Exception as e:
        st.error(f"Fatal Error: Could not load frequency maps. Please ensure 'frequency_maps.txt' is in the correct directory. Details: {e}")
        return model, None
        
    return model, freq_maps

model, FREQUENCY_MAPS = load_model_and_maps()

# --- DATABASE FUNCTIONS ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg2.connect(PG_CONN_STRING)

def fetch_claim_by_id(claim_id):
    """Fetches a single claim's details from the database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        # Fetch all columns to populate the form
        cur.execute("SELECT * FROM claims WHERE id = %s", (claim_id,))
        claim = cur.fetchone()
        cur.close()
        conn.close()
        return dict(claim) if claim else None
    except Exception as e:
        st.error(f"Database Error: Could not fetch claim {claim_id}. Details: {e}")
        return None

def fetch_dashboard_stats():
    """Fetches summary statistics for the dashboard."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT COUNT(*) as total_claims, SUM(claim_amount) as total_amount FROM claims;")
        stats = cur.fetchone()
        cur.execute("SELECT COUNT(*) as high_risk_claims FROM claims WHERE risk_label = 'High Risk';")
        high_risk = cur.fetchone()
        cur.close()
        conn.close()
        return {
            "total_claims": stats['total_claims'] or 0,
            "total_amount": stats['total_amount'] or 0,
            "high_risk_claims": high_risk['high_risk_claims'] or 0
        }
    except Exception as e:
        st.error(f"Database Error: Could not fetch dashboard stats. Details: {e}")
        return {"total_claims": 0, "total_amount": 0, "high_risk_claims": 0}

def update_claim_prediction(claim_id, risk_score, risk_label, model_output):
    """Updates an existing claim with new prediction results."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        sql = "UPDATE claims SET risk_score = %s, risk_label = %s, model_output = %s WHERE id = %s;"
        cur.execute(sql, (risk_score, risk_label, model_output, claim_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database Error: Could not update claim {claim_id}. Details: {e}")
        return False

# --- PREDICTION LOGIC ---
def predict_fraud(claim_data):
    """Preprocesses data and runs the fraud detection model."""
    if not model or not FREQUENCY_MAPS:
        return {"error": "Model or frequency maps are not loaded."}
    try:
        def to_float(v): return float(v) if v is not None and v != '' else 0.0
        def get_freq(m, v): return FREQUENCY_MAPS.get(m, {}).get(str(v), 1)
        gender_map = {'Male': 1, 'Female': 2}
        race_map = {'White': 1, 'Black': 2, 'Other': 3, 'Asian': 4, 'Hispanic': 5}

        # RECTIFIED: This logic now builds the feature vector in the exact order required by the model,
        # mapping from the model's expected names to the lowercase names from the form/DB.
        feature_vector_map = {}
        for model_col_name in MODEL_FEATURE_COLUMNS:
            # Determine the lowercase key used in the form/database by stripping suffixes and lowercasing
            form_key = model_col_name.replace('_freq_encoded', '').lower()
            # Handle specific known column name differences between model and DB/form
            if form_key == "ipannualreimbursedamt": form_key = "ipannualreimbursementamt" # Fix typo from error log
            if form_key == "noofmonths_partacov": form_key = "noofmonths_partacov"
            if form_key == "noofmonths_partbcov": form_key = "noofmonths_partbcov"
            if form_key == "provider": form_key = "provider"
            if form_key == "chroniccond_osteoporosis": form_key = "chroniccond_osteoporasis" # Match form typo
            
            value = claim_data.get(form_key)

            # Apply the correct preprocessing based on the model's required column name
            if model_col_name == 'Gender':
                feature_vector_map[model_col_name] = float(gender_map.get(value, 0))
            elif model_col_name == 'Race':
                feature_vector_map[model_col_name] = float(race_map.get(value, 0))
            elif model_col_name == 'RenalDiseaseIndicator':
                feature_vector_map[model_col_name] = 1.0 if value == 'Y' else 0.0
            elif model_col_name.endswith('_freq_encoded'):
                # The key for the frequency map is the feature name without the suffix
                freq_map_key = model_col_name.replace('_freq_encoded', '')
                feature_vector_map[model_col_name] = get_freq(freq_map_key, value)
            else:
                feature_vector_map[model_col_name] = to_float(value)

        # Create the DataFrame with the exact column names the model expects
        feature_df = pd.DataFrame([feature_vector_map], columns=MODEL_FEATURE_COLUMNS)
        dmatrix = xgb.DMatrix(feature_df, feature_names=MODEL_FEATURE_COLUMNS)
        
        probability_fraud = model.predict(dmatrix)[0]
        
        risk_score = int(probability_fraud * 100)
        risk_label = "High Risk" if risk_score > 75 else "Medium Risk" if risk_score > 40 else "Low Risk"
        
        return {
            "risk_score": risk_score,
            "risk_label": risk_label,
            "model_output": json.dumps({"prediction": float(probability_fraud)})
        }
    except Exception as e:
        return {"error": f"An error occurred during prediction. Details: {e}"}

# --- UI LAYOUT ---

# Initialize session state for multi-step forms
if 'claim_data' not in st.session_state:
    st.session_state.claim_data = {}
if 'prediction_result' not in st.session_state:
    st.session_state.prediction_result = None

# Sidebar Navigation
st.sidebar.title("🛡️ SecureClaim AI")
page = st.sidebar.radio(
    "Navigation",
    ("🏠 Home", "🔍 New Analysis", "📊 Dashboard"),
    label_visibility="collapsed"
)
st.sidebar.markdown("---")
st.sidebar.info("This application uses an XGBoost model to detect potentially fraudulent insurance claims.")

# --- PAGE 1: HOME ---
if page == "🏠 Home":
    st.title("Welcome to SecureClaim AI")
    st.markdown("### Advanced Fraud Detection Powered by Machine Learning")
    st.write(
        "This tool provides a powerful interface to analyze insurance claims in real-time. "
        "Navigate using the sidebar to analyze a new or existing claim, or to view the overall dashboard."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("#### **🔍 Analyze a Claim**")
        st.write(
            "Enter details for a new claim or load an existing claim by its ID. "
            "Our model will process the information and provide a fraud risk assessment instantly."
        )
    with col2:
        st.info("#### **📊 View Dashboard**")
        st.write(
            "Get a high-level overview of all claims processed. Track key metrics like "
            "total claims, total amount claimed, and the number of high-risk cases identified."
        )

# --- PAGE 2: NEW ANALYSIS ---
elif page == "🔍 New Analysis":
    st.title("Analyze a Claim")
    
    # --- Part 1: Load or Input Data ---
    input_method = st.radio("Choose Input Method", ["Load Existing Claim by ID", "Enter New Claim Details"], horizontal=True)

    if input_method == "Load Existing Claim by ID":
        claim_id_to_load = st.number_input("Enter Claim ID to load and re-analyze", min_value=1, step=1)
        if st.button("Load Claim Data"):
            with st.spinner("Fetching claim from database..."):
                data = fetch_claim_by_id(claim_id_to_load)
                if data:
                    st.session_state.claim_data = data
                    st.session_state.prediction_result = None # Clear previous results
                    st.success(f"Successfully loaded data for Claim ID: {claim_id_to_load}")
                else:
                    st.session_state.claim_data = {}
                    st.error(f"No claim found with ID: {claim_id_to_load}")
    else: # Enter New Claim Details
        if st.button("Clear Form"):
            st.session_state.claim_data = {}
            st.session_state.prediction_result = None
    
    # --- Part 2: The Form (populated by session state) ---
    st.markdown("---")
    st.subheader("Claim Details Form")
    
    def get_state(key, default=''):
        val = st.session_state.claim_data.get(key, default)
        if isinstance(val, Decimal): return float(val)
        if isinstance(val, date): return val
        return val if val is not None else default

    with st.form("claim_form"):
        st.write("**Patient & Claim Information**")
        c1, c2, c3, c4 = st.columns(4)
        with c1: beneid = st.text_input("BeneID", get_state('beneid'))
        with c2:
            gender_options = ["", "Male", "Female"]
            gender_val = get_state('gender', '')
            gender_index = gender_options.index(gender_val) if gender_val in gender_options else 0
            gender = st.selectbox("Gender", gender_options, index=gender_index)
        with c3:
            race_options = ["", "White", "Black", "Other", "Asian", "Hispanic"]
            race_val = get_state('race', '')
            race_index = race_options.index(race_val) if race_val in race_options else 0
            race = st.selectbox("Race", race_options, index=race_index)
        with c4:
            renal_options = ["", "Y", "N"]
            renal_val = get_state('renaldiseaseindicator', '')
            renal_index = renal_options.index(renal_val) if renal_val in renal_options else 0
            renaldiseaseindicator = st.selectbox("Renal Disease", renal_options, index=renal_index)

        st.write("**Provider Information**")
        c1, c2, c3, c4 = st.columns(4)
        with c1: provider = st.text_input("Provider", get_state('provider'))
        with c2: attendingphysician = st.text_input("Attending Physician", get_state('attendingphysician'))
        with c3: operatingphysician = st.text_input("Operating Physician", get_state('operatingphysician'))
        with c4: otherphysician = st.text_input("Other Physician", get_state('otherphysician'))
        
        st.write("**Location & Diagnosis**")
        c1, c2, c3 = st.columns(3)
        with c1: state = st.text_input("State", get_state('state'))
        with c2: county = st.text_input("County", get_state('county'))
        with c3: diagnosisgroupcode = st.text_input("Diagnosis Group Code", get_state('diagnosisgroupcode'))
        
        st.write("**Claim Amounts**")
        c1, c2, c3, c4 = st.columns(4)
        with c1: inscclaimamtreimbursed = st.number_input("Amount Reimbursed", value=get_state('inscclaimamtreimbursed', 0.0), format="%.2f")
        with c2: deductibleamtpaid = st.number_input("Deductible Paid", value=get_state('deductibleamtpaid', 0.0), format="%.2f")
        with c3: ipannualreimbursementamt = st.number_input("IP Annual Reimbursement", value=get_state('ipannualreimbursementamt', 0.0), format="%.2f")
        with c4: ipannualdeductibleamt = st.number_input("IP Annual Deductible", value=get_state('ipannualdeductibleamt', 0.0), format="%.2f")
        c1, c2, c3, c4 = st.columns(4)
        with c1: opannualreimbursementamt = st.number_input("OP Annual Reimbursement", value=get_state('opannualreimbursementamt', 0.0), format="%.2f")
        with c2: opannualdeductibleamt = st.number_input("OP Annual Deductible", value=get_state('opannualdeductibleamt', 0.0), format="%.2f")

        st.write("**Coverage Months**")
        c1, c2 = st.columns(2)
        with c1: noofmonths_partacov = st.number_input("Months Part A Cov", value=get_state('noofmonths_partacov', 0), step=1)
        with c2: noofmonths_partbcov = st.number_input("Months Part B Cov", value=get_state('noofmonths_partbcov', 0), step=1)
        
        with st.expander("Chronic Conditions (Select 1 for Yes, 0 for No)"):
            def get_safe_cond_index(key):
                val = get_state(key, 0)
                return 1 if str(val) in ['1', 'True'] else 0
            
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: chroniccond_alzheimer = st.selectbox("Alzheimer", [0, 1], index=get_safe_cond_index('chroniccond_alzheimer'))
            with c2: chroniccond_heartfailure = st.selectbox("Heart Failure", [0, 1], index=get_safe_cond_index('chroniccond_heartfailure'))
            with c3: chroniccond_kidneydisease = st.selectbox("Kidney Disease", [0, 1], index=get_safe_cond_index('chroniccond_kidneydisease'))
            with c4: chroniccond_cancer = st.selectbox("Cancer", [0, 1], index=get_safe_cond_index('chroniccond_cancer'))
            with c5: chroniccond_obstrpulmonary = st.selectbox("Obstr. Pulmonary", [0, 1], index=get_safe_cond_index('chroniccond_obstrpulmonary'))
            
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: chroniccond_depression = st.selectbox("Depression", [0, 1], index=get_safe_cond_index('chroniccond_depression'))
            with c2: chroniccond_diabetes = st.selectbox("Diabetes", [0, 1], index=get_safe_cond_index('chroniccond_diabetes'))
            with c3: chroniccond_ischemicheart = st.selectbox("Ischemic Heart", [0, 1], index=get_safe_cond_index('chroniccond_ischemicheart'))
            # RECTIFIED: Corrected the key to match the form data dictionary
            with c4: chroniccond_osteoporasis = st.selectbox("Osteoporosis", [0, 1], index=get_safe_cond_index('chroniccond_osteoporasis'))
            with c5: chroniccond_rheumatoidarthritis = st.selectbox("Rheumatoid Arthritis", [0, 1], index=get_safe_cond_index('chroniccond_rheumatoidarthritis'))
            
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: chroniccond_stroke = st.selectbox("Stroke", [0, 1], index=get_safe_cond_index('chroniccond_stroke'))

        submitted = st.form_submit_button("Analyze Fraud Risk")

        if submitted:
            form_data = {
                "beneid": beneid, "gender": gender, "race": race, "renaldiseaseindicator": renaldiseaseindicator,
                "provider": provider, "attendingphysician": attendingphysician, "operatingphysician": operatingphysician, "otherphysician": otherphysician,
                "state": state, "county": county, "diagnosisgroupcode": diagnosisgroupcode,
                "inscclaimamtreimbursed": inscclaimamtreimbursed, "deductibleamtpaid": deductibleamtpaid,
                "ipannualreimbursementamt": ipannualreimbursementamt, "ipannualdeductibleamt": ipannualdeductibleamt,
                "opannualreimbursementamt": opannualreimbursementamt, "opannualdeductibleamt": opannualdeductibleamt,
                "noofmonths_partacov": noofmonths_partacov, "noofmonths_partbcov": noofmonths_partbcov,
                "chroniccond_alzheimer": chroniccond_alzheimer, "chroniccond_heartfailure": chroniccond_heartfailure,
                "chroniccond_kidneydisease": chroniccond_kidneydisease, "chroniccond_cancer": chroniccond_cancer,
                "chroniccond_obstrpulmonary": chroniccond_obstrpulmonary, "chroniccond_depression": chroniccond_depression,
                "chroniccond_diabetes": chroniccond_diabetes, "chroniccond_ischemicheart": chroniccond_ischemicheart,
                # RECTIFIED: Corrected the key to match what the prediction function expects
                "chroniccond_osteoporasis": chroniccond_osteoporasis, 
                "chroniccond_rheumatoidarthritis": chroniccond_rheumatoidarthritis,
                "chroniccond_stroke": chroniccond_stroke
            }
            
            with st.spinner("Analyzing claim..."):
                result = predict_fraud(form_data)
                st.session_state.prediction_result = result
                if "error" not in result:
                    if st.session_state.claim_data.get('id'):
                        claim_id = st.session_state.claim_data.get('id')
                        update_claim_prediction(claim_id, result['risk_score'], result['risk_label'], result['model_output'])
    
    if st.session_state.prediction_result:
        st.markdown("---")
        st.subheader("Analysis Result")
        result = st.session_state.prediction_result
        
        if "error" in result:
            st.error(result["error"])
        else:
            score = result['risk_score']
            label = result['risk_label']
            
            if label == "High Risk":
                st.error(f"**Result: {label}**")
            elif label == "Medium Risk":
                st.warning(f"**Result: {label}**")
            else:
                st.success(f"**Result: {label}**")
            
            st.metric(label="Fraud Risk Score", value=f"{score}%")
            st.progress(score)
            
            with st.expander("View Raw Model Output"):
                st.json(result['model_output'])

# --- PAGE 3: DASHBOARD ---
elif page == "📊 Dashboard":
    st.title("Claims Dashboard")
    
    with st.spinner("Loading dashboard data..."):
        stats = fetch_dashboard_stats()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Claims Processed", f"{stats['total_claims']:,}")
    col2.metric("Total Amount Claimed", f"₹{stats['total_amount']:,.2f}")
    col3.metric("High-Risk Claims Identified", f"{stats['high_risk_claims']:,}")

    st.info("More charts and detailed analysis can be added here.")

