🛡️ SecureClaim AI: Advanced Fraud Detection System
SecureClaim AI is a full-stack web application designed to detect fraudulent insurance claims in real-time. It leverages a powerful XGBoost machine learning model to provide a comprehensive solution, from data submission and analysis to a rich dashboard for tracking financial impact and ROI.

✨ Key Features
🤖 AI-Powered Analysis: Utilizes a sophisticated XGBoost model to analyze hundreds of data points and identify subtle patterns indicative of fraud.

⚡ Real-Time Detection: Assess the risk of a claim as it is submitted, allowing for immediate action before funds are disbursed.

📊 Interactive Dashboard: A comprehensive ROI dashboard to track key metrics like total savings, claims processed, and fraudulent claims detected.

📈 Detailed Results: Get a clear risk score, a human-readable risk label (Low, Medium, High), and a visual breakdown of the model's prediction confidence for each claim.

📂 Full-Stack Application: Includes a user-friendly frontend, a robust Flask backend API, and a PostgreSQL database.

🏗️ System Architecture
The application follows a classic three-tier architecture:

+-----------------+      +------------------------+      +-------------------+
|   Frontend      |      |   Backend (Flask API)  |      |   Data Layer      |
| (HTML, CSS, JS) | <--> | (app.py)               | <--> | (PostgreSQL DB)   |
+-----------------+      +------------------------+      +-------------------+
                         |           |            |
                         |           v            |
                         | +--------------------+ |
                         | | ML Model (XGBoost) | |
                         | +--------------------+ |

Frontend: A static web interface where users can submit new claims for analysis or look up the results of existing claims.

Backend (Flask API): The core of the application. It handles incoming requests, interacts with the database, and calls the machine learning model to perform fraud analysis.

Data Layer: A PostgreSQL database running in a Docker container stores all claim information, including the results of the fraud analysis.

🛠️ Technology Stack
Category

Technologies

Backend

Python, Flask, Flask-CORS

Database

PostgreSQL

ML & Data

Scikit-learn, XGBoost, Pandas, NumPy

Frontend

HTML5, CSS3, JavaScript, Chart.js

Containerization

Docker

🚀 Getting Started
Follow these instructions to get a local copy of the project up and running on your machine for development and testing purposes.

Prerequisites
Python 3.8+

Docker installed and running.

⚙️ Setup and Installation
1. Clone the Repository
git clone [https://github.com/your-username/SecureClaim-AI.git](https://github.com/your-username/SecureClaim-AI.git)
cd SecureClaim-AI

2. Set Up the Backend
Create and activate a Python virtual environment:

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate

Install the required Python packages from requirements.txt:

pip install -r requirements.txt

3. Set Up the PostgreSQL Database with Docker
We will use Docker to run a PostgreSQL instance in a container. This ensures a clean and isolated environment for the database. From the root of the project directory, run:

docker run --name fraud-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=fraud_detection -p 5432:5432 -d postgres

This command will:

--name fraud-db: Name the container fraud-db.

-e POSTGRES_USER=postgres: Set the database user.

-e POSTGRES_PASSWORD=password: Set the database password.

-e POSTGRES_DB=fraud_detection: Create an initial database.

-p 5432:5432: Map port 5432 on your local machine to port 5432 in the container.

-d postgres: Run the official PostgreSQL image in detached mode.

Your database is now running! You can verify the connection with python connection_test.py.

4. Initialize the Database Schema
Run the provided SQL script to create the claims table in your new database. You may need to have psql installed or use a GUI tool like DBeaver.

psql -h localhost -U postgres -d fraud_detection -f db_init.sql

(You will be prompted for the password, which is password)

5. Load the Sample Data
Place the provided dataset (test_data.xlsx) in the project's root directory. Then, run the datafeed.py script to populate the database:

python datafeed.py

▶️ Running the Application
Start the Flask Backend Server:

python app.py

The backend API will now be running at http://127.0.0.1:5000.

Access the Frontend:
Open the Home.html file directly in your web browser.

You can now use the application to analyze claims!

📖 API Endpoints
The backend provides the following RESTful API endpoints:

Method

Endpoint

Description

POST

/api/submit

Submits a new claim, analyzes it, and stores it.

POST

/api/analyze/<claim_id>

Re-runs the fraud analysis on an existing claim.

GET

/api/result/<claim_id>

Retrieves the details and analysis for a claim.

GET

/api/dashboard

Fetches aggregated statistics for the dashboard.

📁 Project Structure
.
├── app.py                      # Main Flask application file
├── app5.py                     # Core prediction logic
├── datafeed.py                 # Script to load data into the DB
├── db_init.sql                 # SQL schema for the 'claims' table
├── requirements.txt            # Python dependencies
|
├── xgboost_final_model.json    # Pre-trained XGBoost model
├── frequency_maps.txt          # Frequency encoding maps for the model
|
├── Home.html                   # Main landing page
├── Input.html                  # Page for submitting claims
├── Result.html                 # Page to display analysis results
└── Dashboard.html              # ROI and statistics dashboard

🤝 Contributing
Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)

Commit your Changes (git commit -m 'Add some AmazingFeature')

Push to the Branch (git push origin feature/AmazingFeature)

Open a Pull Request

📜 License
This project is licensed under the MIT License. See the LICENSE file for details.
