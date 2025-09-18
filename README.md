# 🛡️ SecureClaim AI: Advanced Fraud Detection System

SecureClaim AI is a **full-stack web application** designed to detect fraudulent insurance claims in real time.  
It leverages a powerful **XGBoost machine learning model** to provide an end-to-end solution — from claim submission and analysis to interactive dashboards that track financial impact and ROI.

---

## ✨ Key Features

- 🤖 **AI-Powered Analysis**  
  Sophisticated XGBoost model that analyzes hundreds of data points to identify subtle fraud patterns.

- ⚡ **Real-Time Detection**  
  Assess claim risk immediately at submission to prevent fraudulent payouts.

- 📊 **Interactive Dashboard**  
  Track key metrics like **total savings, claims processed, and fraud detected** with visual insights.

- 📈 **Detailed Results**  
  Each claim includes a **risk score**, a human-readable **risk label** (Low, Medium, High), and a **visual breakdown of prediction confidence**.

- 📂 **Full-Stack Application**  
  User-friendly **frontend**, robust **Flask backend API**, and a **PostgreSQL database**.

---

## 🏗️ System Architecture

The system follows a classic **three-tier architecture**:
```graphql
+-----------------+      +------------------------+      +-------------------+
|   Frontend      |      |   Backend (Flask API)  |      |   Data Layer      |
| (HTML, CSS, JS) | <--> | (app.py)               | <--> | (PostgreSQL DB)   |
+-----------------+      +------------------------+      +-------------------+
                         |           |            |
                         |           v            |
                         | +--------------------+ |
                         | | ML Model (XGBoost) | |
                         | +--------------------+ |
```


- **Frontend**: Static web interface for claim submission and results lookup.  
- **Backend (Flask API)**: Core application logic, ML model integration, DB interaction.  
- **Data Layer**: PostgreSQL (Dockerized) storing claim records and fraud analysis results.  

---

## 🛠️ Technology Stack

| Category        | Technologies |
|-----------------|--------------|
| **Backend**     | Python, Flask, Flask-CORS |
| **Database**    | PostgreSQL |
| **ML & Data**   | Scikit-learn, XGBoost, Pandas, NumPy |
| **Frontend**    | HTML5, CSS3, JavaScript, Chart.js |
| **Containerization** | Docker |

---

## 🚀 Getting Started

### Prerequisites
- Python **3.8+**
- Docker installed and running

---

### ⚙️ Setup and Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/Hospital-FraudClaim-Detection.git
   cd Hospital-FraudClaim-Detection
   ```

2. **Setup the backend**
   - Create and activate a virtual environment

   ##### macOS/Linux
   ```bash
      python3 -m venv venv
      source venv/bin/activate
    ```
    ##### Windows
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
   **Install Dependencies:**
   
    ```python
    pip install -r requirements.txt
    ```

4. **Run PostgreSQL with Docker**

      ```bash
      docker run --name fraud-db \
      -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=password \
      -e POSTGRES_DB=fraud_detection \
      -p 5432:5432 -d postgres
      ```
    - Verify the DB connection with:

      ```python
      python connection_test.py
      ```

5. **Initialize the DataBase Schema**

      ```bash
      psql -h localhost -U postgres -d fraud_detection -f db_init.sql
      # Password: password
      ```
6. **Load Sample Data**

      - Place **test_data.xlsx** in the directory
      - Run:
        ```python
        python datafeed.py
        ```
7. **▶️ Running the Application**

      - Start the Backend:
        ```Python
          python app.py
        ```
      - Backend Runs at: http://127.0.0.1:5000
        (May vary)
      - Open the Frontend
          - Launch **localhost:5000** on your browser

8. **📁 Project Structure**

   ```graphql
    ├── app3.py                     # Main Flask application
    ├── app4.py                     # Streamlit application
    ├── datafeed.py                 # Script to load DB data
    ├── db_init.sql                 # Schema for 'claims' table
    ├── requirements.txt            # Dependencies
    │
    ├── xgboost_final_model.json    # Pre-trained XGBoost model
    ├── frequency_maps.txt          # Frequency encoding maps
    │
    ├── Home.html                   # Landing page
    ├── Input.html                  # Claim submission page
    ├── Result.html                 # Claim analysis results
    └── Dashboard.html              # ROI and statistics dashboard
    ```



