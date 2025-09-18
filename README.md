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

+-----------------+ +------------------------+ +-------------------+
| Frontend | | Backend (Flask API) | | Data Layer |
| (HTML, CSS, JS) | <--> | (app.py) | <--> | (PostgreSQL DB) |
+-----------------+ +------------------------+ +-------------------+
| | |
| v |
| +--------------------+ |
| | ML Model (XGBoost) | |
| +--------------------+ |
