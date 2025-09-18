import pandas as pd
import psycopg2
import json
import numpy as np

# --- CONFIGURATION ---
EXCEL_FILE_PATH = 'test_data.xlsx' 
PG_CONN_STRING = "postgresql://postgres:password@localhost:5432/fraud_detection"

def import_data():
    """
    Reads data from an Excel file and inserts it into the PostgreSQL database.
    """
    try:
        print(f"🔄 Reading data from '{EXCEL_FILE_PATH}'...")
        df = pd.read_excel(EXCEL_FILE_PATH)
        df = df.replace({np.nan: None})
        print(f"✅ Found {len(df)} rows to import.")
    except FileNotFoundError:
        print(f"❌ ERROR: The file was not found at '{EXCEL_FILE_PATH}'. Please check the path and try again.")
        return
    except Exception as e:
        print(f"❌ ERROR: Failed to read the Excel file. Details: {e}")
        return

    conn = None
    try:
        print("🔄 Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(PG_CONN_STRING)
        cur = conn.cursor()
        print("✅ Database connection successful.")

        # Define main columns
        main_columns = ['BeneID', 'ClaimID', 'ClaimStartDt', 'ClaimEndDt', 'Provider',
       'InscClaimAmtReimbursed', 'AttendingPhysician', 'OperatingPhysician',
       'OtherPhysician', 'AdmissionDt', 'ClmAdmitDiagnosisCode',
       'DeductibleAmtPaid', 'DischargeDt', 'DiagnosisGroupCode',
       'ClmDiagnosisCode_1', 'ClmDiagnosisCode_2', 'ClmDiagnosisCode_3',
       'ClmDiagnosisCode_4', 'ClmDiagnosisCode_5', 'ClmDiagnosisCode_6',
       'ClmDiagnosisCode_7', 'ClmDiagnosisCode_8', 'ClmDiagnosisCode_9',
       'ClmDiagnosisCode_10', 'ClmProcedureCode_1', 'ClmProcedureCode_2',
       'ClmProcedureCode_3', 'ClmProcedureCode_4', 'ClmProcedureCode_5',
       'ClmProcedureCode_6', 'DOB', 'DOD', 'Gender', 'Race',
       'RenalDiseaseIndicator', 'State', 'County', 'NoOfMonths_PartACov',
       'NoOfMonths_PartBCov', 'ChronicCond_Alzheimer',
       'ChronicCond_Heartfailure', 'ChronicCond_KidneyDisease',
       'ChronicCond_Cancer', 'ChronicCond_ObstrPulmonary',
       'ChronicCond_Depression', 'ChronicCond_Diabetes',
       'ChronicCond_IschemicHeart', 'ChronicCond_Osteoporasis',
       'ChronicCond_rheumatoidarthritis', 'ChronicCond_stroke',
       'IPAnnualReimbursementAmt', 'IPAnnualDeductibleAmt',
       'OPAnnualReimbursementAmt', 'OPAnnualDeductibleAmt']

        # Add the JSON column
        all_columns = main_columns + ["model_features"]

        # Build SQL dynamically
        placeholders = ", ".join(["%s"] * len(all_columns))
        insert_sql = f"""
            INSERT INTO claims ({", ".join(all_columns)})
            VALUES ({placeholders});
        """

        print("🔄 Starting data import process...")
        for index, row in df.iterrows():
            # 1. Main column values
            main_values = tuple(row.get(col) for col in main_columns)

            # 2. JSON for remaining columns
            model_features = {
                col: row[col] for col in df.columns if col not in main_columns
            }
            model_features_json = json.dumps(model_features, default=str)

            # 3. Final values tuple
            values = main_values + (model_features_json,)

            # 4. Execute insert
            cur.execute(insert_sql, values)

            if (index + 1) % 1000 == 0:  # progress update every 1000 rows
                print(f"  -> Imported {index + 1}/{len(df)} rows...")

        conn.commit()
        print("\n✅✅ Import complete! All data has been successfully saved to the database.")

    except (Exception, psycopg2.Error) as error:
        print(f"❌ ERROR: Failed to insert data into the database. Details: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()
            print("🚪 Database connection closed.")

if __name__ == "__main__":
    import_data()
