import joblib
import numpy as np
import logging
from typing import List, Union
import xgboost as xgb

# Configure logging to create 'model_logs.log' in the same directory (Backend)
logging.basicConfig(
    filename="model_logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class ModelWrapper:
    def __init__(self, model_path: str = "", scaler_path: str = ""):
        """
        Initializes the ModelWrapper by loading the ML model from its native format
        to ensure version compatibility and stability.
        """
        try:
            # Instantiate the correct XGBoost model type before loading its state
            self.model = xgb.XGBClassifier()  # Use xgb.XGBRegressor() for regression tasks
            self.model.load_model(model_path)
            logging.info("✅ Model loaded successfully from %s", model_path)
            
            # Load the scaler using joblib if a path is provided
            self.scaler = joblib.load(scaler_path) if scaler_path else None
            if self.scaler:
                logging.info("✅ Scaler loaded successfully from %s", scaler_path)

        except FileNotFoundError as e:
            logging.error("❌ CRITICAL: Model or scaler file not found. Ensure '%s' is in the Backend folder. Error: %s", model_path, str(e))
            raise e
        except Exception as e:
            logging.error("❌ CRITICAL: Failed to load model. Error: %s", str(e))
            raise e

    def preprocess(self, input_data: List[Union[int, float]]) -> np.ndarray:
        """
        Preprocesses the input data before making a prediction.
        - Ensures the data is in the correct NumPy array format for the model.
        - Applies a scaler transformation if a scaler was loaded.
        """
        try:
            # Convert the input list to a NumPy array and reshape for a single prediction
            input_array = np.array(input_data).reshape(1, -1)
            
            if self.scaler:
                input_array = self.scaler.transform(input_array)
            
            logging.info("✅ Input preprocessed successfully.")
            return input_array
        except Exception as e:
            logging.error("❌ Preprocessing failed: %s", str(e))
            raise e

    def predict(self, input_data: List[Union[int, float]]) -> dict:
        """
        Takes a list of features, preprocesses them, and returns a dictionary
        containing the model's prediction and the class probabilities.
        """
        try:
            # Preprocess the raw input data to prepare it for the model
            processed_data = self.preprocess(input_data)
            
            # Get the final prediction (e.g., 0 for Not Fraud, 1 for Fraud)
            prediction = self.model.predict(processed_data)[0]
            
            # Get the prediction probabilities if the model supports it
            probabilities = None
            if hasattr(self.model, "predict_proba"):
                # Returns probabilities for each class, e.g., [P(class_0), P(class_1)]
                probabilities = self.model.predict_proba(processed_data)[0].tolist()

            # Structure the final result
            result = {
                "prediction": int(prediction),
                "probabilities": probabilities
            }

            logging.info("✅ Prediction successful: %s", result)
            return result
        except Exception as e:
            logging.error("❌ Prediction failed: %s", str(e))
            return {"error": str(e)}

