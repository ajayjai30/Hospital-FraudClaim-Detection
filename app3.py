# app.py
import json
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import DictCursor
from model_wrapper import ModelWrapper  # Import the model wrapper

# --- CONFIGURATION ---
PG_CONN_STRING = "postgresql://postgres:password@localhost:5432/fraud_detection"
FLASK_PORT = 5000

# --- ML Model & Preprocessing Setup ---
try:
    with open('frequency_maps.txt', 'r') as f:
        FREQUENCY_MAPS = json.load(f)
    print("✅ Frequency encoding maps loaded successfully.")
except Exception as e:
    print(f"❌ CRITICAL: Could not load 'frequency_maps.txt'. Error: {e}")
    FREQUENCY_MAPS = {}

try:
    model = ModelWrapper(model_path="xgboost_final_model.json")
    print("✅ Machine learning model loaded successfully.")
except Exception as e:
    print(f"❌ CRITICAL: Could not load model. Error: {e}")
    model = None

# --- Flask setup ---
app = Flask(__name__, static_folder="../Frontend", static_url_path="")
CORS(app)


def get_db_connection():
    return psycopg2.connect(PG_CONN_STRING)


def init_db():
    """Initialize database connection (optional schema setup)."""
    print("🔍 Connecting to PostgreSQL...")
    try:
        conn = get_db_connection()
        print("✅ Connected to PostgreSQL database.")
        cur = conn.cursor()
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ DB init error: {e}")


def predict_fraud(claim_data):
    """Preprocesses raw claim data and returns a fraud prediction."""
    if not model or not FREQUENCY_MAPS:
        return {"error": "Model or frequency maps not available."}
    try:
        def to_float(v): return float(v) if v is not None and v != '' else 0.0
        def get_freq(m, v): return FREQUENCY_MAPS.get(m, {}).get(str(v), 1)

        gender_map = {'Male': 1, 'Female': 2}
        race_map = {'White': 1, 'Black': 2, 'Other': 3, 'Asian': 4, 'Hispanic': 5}

        feature_vector = [
            to_float(claim_data.get("InscClaimAmtReimbursed")),
            to_float(claim_data.get("DeductibleAmtPaid")),
            float(gender_map.get(claim_data.get('Gender'), 0)),
            float(race_map.get(claim_data.get('Race'), 0)),
            to_float(claim_data.get("RenalDiseaseIndicator")),
            get_freq('State', claim_data.get('State')),
            get_freq('County', claim_data.get('County')),
            to_float(claim_data.get("NoOfMonth_PartACov")),
            to_float(claim_data.get("NoOfMonth_PartBCov")),
            to_float(claim_data.get("ChronicCond_Alzheimer")),
            to_float(claim_data.get("ChronicCond_Heartfailure")),
            to_float(claim_data.get("ChronicCond_KidneyDisease")),
            to_float(claim_data.get("ChronicCond_Cancer")),
            to_float(claim_data.get("ChronicCond_ObstrPulmonary")),
            to_float(claim_data.get("ChronicCond_Depression")),
            to_float(claim_data.get("ChronicCond_Diabetes")),
            to_float(claim_data.get("ChronicCond_IschemicHeart")),
            to_float(claim_data.get("ChronicCond_Osteoporosis")),
            to_float(claim_data.get("ChronicCond_rheumatoidarthritis")),
            to_float(claim_data.get("ChronicCond_stroke")),
            to_float(claim_data.get("IPAnnualReimbursementAmt")),
            to_float(claim_data.get("IPAnnualDeductibleAmt")),
            to_float(claim_data.get("OPAnnualReimbursementAmt")),
            to_float(claim_data.get("OPAnnualDeductibleAmt")),
            get_freq('BeneID', claim_data.get('BeneID')),
            get_freq('Provider', claim_data.get('provider_id')),
            get_freq('AttendingPhysician', claim_data.get('AttendingPhysician')),
            get_freq('OperatingPhysician', claim_data.get('OperatingPhysician')),
            get_freq('OtherPhysician', claim_data.get('OtherPhysician')),
            get_freq('DiagnosisGroupCode', claim_data.get('DiagnosisGroupCode')),
        ]

        prediction_output = model.predict(feature_vector)
        probabilities = prediction_output.get("probabilities", [0, 0])
        risk_score = int(probabilities[1] * 100) if len(probabilities) > 1 else 0
        risk_label = "High Risk" if risk_score > 75 else "Medium Risk" if risk_score > 40 else "Low Risk"

        return {
            "risk_score": risk_score,
            "risk_label": risk_label,
            "model_output": json.dumps(prediction_output)
        }
    except Exception as e:
        print(f"❌ Error during prediction: {e}")
        return {"error": str(e)}


# --- ROUTES ---
@app.route('/')
def root():
    return send_from_directory(app.static_folder, "Home.html")


@app.route('/<path:filename>')
def serve_page(filename):
    return send_from_directory(app.static_folder, filename)


@app.route('/api/submit', methods=['POST'])
def submit_claim():
    try:
        data = request.get_json(force=True)
        prediction_results = predict_fraud(data)
        if "error" in prediction_results:
            return jsonify(prediction_results), 500

        conn = get_db_connection()
        cur = conn.cursor()

        columns = data.keys()
        columns_sql = ", ".join(columns) + ", risk_score, risk_label, model_output"
        placeholders_sql = ", ".join(["%s"] * (len(columns) + 3))

        values = list(data.values())
        values.extend([
            prediction_results['risk_score'],
            prediction_results['risk_label'],
            prediction_results['model_output']
        ])

        insert_sql = f"INSERT INTO claims ({columns_sql}) VALUES ({placeholders_sql}) RETURNING id;"
        cur.execute(insert_sql, tuple(values))
        claim_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"claim_id": claim_id}), 201
    except Exception as e:
        print(f"❌ ERROR in submit_claim: {e}")
        return jsonify({"error": str(e), "trace": "submit_claim"}), 500


@app.route('/api/analyze/<int:claim_id>', methods=['POST'])
def analyze_claim(claim_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT * FROM claims WHERE id = %s", (claim_id,))
        claim = cur.fetchone()
        if not claim:
            cur.close(), conn.close()
            return jsonify({"error": "Claim not found", "id": claim_id}), 404

        prediction_results = predict_fraud(dict(claim))
        if "error" in prediction_results:
            cur.close(), conn.close()
            return jsonify(prediction_results), 500

        update_sql = "UPDATE claims SET risk_score = %s, risk_label = %s, model_output = %s WHERE id = %s;"
        cur.execute(update_sql, (
            prediction_results['risk_score'],
            prediction_results['risk_label'],
            prediction_results['model_output'],
            claim_id
        ))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"claim_id": claim_id, "status": "updated"}), 200
    except Exception as e:
        print(f"❌ ERROR in analyze_claim: {e}")
        return jsonify({"error": str(e), "trace": "analyze_claim"}), 500


@app.route('/api/result/<int:claim_id>', methods=['GET'])
def get_result(claim_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT * FROM claims WHERE id = %s", (claim_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return jsonify({"error": "Claim not found", "id": claim_id}), 404
        return jsonify({"claim": dict(row)})
    except Exception as e:
        print(f"❌ ERROR in get_result: {e}")
        return jsonify({"error": str(e), "trace": "get_result"}), 500


# --- MAIN ---
if __name__ == "__main__":
    init_db()
    if model:
        print(f"🚀 Starting server on http://0.0.0.0:{FLASK_PORT}")
        app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)
    else:
        print("❌ Server could not start because the model failed to load.")
