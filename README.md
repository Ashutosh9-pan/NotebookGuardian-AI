# 🛡️ NotebookGuardian AI

> **AI-powered Jupyter Notebook risk analysis and review assistant**

NotebookGuardian AI is a machine-learning-powered tool that analyzes Jupyter Notebook (`.ipynb`) files and identifies cells that may require review based on **code risk** and **execution risk**.

It combines notebook metadata, code structure, execution state, and machine-learning models to provide **cell-level risk scores, explanations, detected signals, and review suggestions** through a modern web dashboard.

---

## 🚀 Live Demo

**Coming soon**

---

## ✨ Features

- 📓 Analyze Jupyter Notebook (`.ipynb`) files
- 🤖 Machine-learning-based risk detection
- 🔍 Dual-risk analysis:
  - **Code Risk**
  - **Execution Risk**
- 📊 Interactive risk distribution dashboard
- 🚨 Cell-level risk scores
- 🏷️ High / Medium / Low risk classification
- 💡 **Why is this flagged?** explanations
- 🔎 Search and risk-level filtering
- 🧩 Full code preview
- 📋 Copy code directly from the preview
- 📄 Generate downloadable PDF analysis reports
- 🔄 Analyze another notebook without refreshing
- ⚡ FastAPI REST API backend
- 🎨 Modern React + Vite frontend
- 🧠 Separate ML models for code and execution risk

---

## 🧠 How It Works

NotebookGuardian AI follows this pipeline:

```text
                 Jupyter Notebook
                        │
                        ▼
                Notebook Upload
                        │
                        ▼
              FastAPI Backend API
                        │
                        ▼
              Notebook Analyzer
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       Code Risk Model      Execution Risk Model
             │                     │
             └──────────┬──────────┘
                        ▼
                 Risk Assessment
                        │
                        ▼
              React Dashboard
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      Risk Scores   Explanations   PDF Report
```

---

## 🔬 Machine Learning

NotebookGuardian AI was developed using notebook-level and cell-level features extracted from Jupyter notebooks.

The feature engineering pipeline includes information such as:

- Source code length
- Number of lines
- Syntax validity
- Assignments
- Function definitions
- Function calls
- Imports
- Conditional statements
- Loops
- Exception handling
- Returns
- Loaded and stored names
- Attributes
- Subscripts
- Constants
- ML-related operations
- File-reading operations
- Execution state
- Execution count
- Previous execution count
- Cell ordering

The project also uses AST-based analysis to extract structural information from Python code.

---

## 📊 Model Performance

### Combined Risk Model

| Model | Accuracy | Precision | Recall | F1 Score |
|---|---:|---:|---:|---:|
| Logistic Regression Baseline | 82.01% | 30.41% | 77.63% | 43.70% |
| Advanced AST Model | 82.84% | 31.15% | 75.00% | 44.02% |
| Selected Feature Model | 83.08% | 31.69% | 76.32% | 44.79% |

Threshold tuning was performed to balance precision and recall for the notebook risk detection workflow.

### Dual-Risk Models

NotebookGuardian AI uses separate models and thresholds for:

**Code Risk**

```text
Threshold: 0.70
```

**Execution Risk**

```text
Threshold: 0.60
```

This allows the system to distinguish between potential code-related concerns and execution/workflow-related concerns.

---

## 📈 Dataset

The ML pipeline was developed using a dataset containing:

- **3,643 notebook cells**
- **111 notebook cases**
- **3,364 normal cells**
- **279 risky cells**

Risk categories include:

- Code/source changes
- Execution changes
- Combined code and execution changes

The project also includes generated feature datasets used during model development and evaluation.

---

## 🖥️ Dashboard

The web application provides an interactive analysis dashboard where users can:

- View notebook summary information
- See overall risk distribution
- Search notebook cells
- Filter cells by risk level
- View individual risk scores
- Inspect code
- Understand why a cell was flagged
- Review recommended actions

---

## 💡 Risk Explanation

For each flagged cell, NotebookGuardian AI provides a **Why is this flagged?** section.

It presents:

- Detected signals
- Risk explanation
- Dominant risk type
- Review suggestion

For dual-risk analysis, the system distinguishes between:

```text
Code Risk
Execution Risk
Both
```

This makes the model output easier to understand instead of showing only a raw probability.

---

## 📄 PDF Reports

NotebookGuardian AI can generate a downloadable PDF report containing:

- Notebook name
- Analysis timestamp
- Model version
- Risk thresholds
- Total code cells
- Flagged cells
- Highest-risk cell
- Risk distribution
- Dual-risk summary
- Highest-risk cells
- Detected reasons
- Review suggestions

---

## 🛠️ Tech Stack

### Frontend

- React
- Vite
- JavaScript
- CSS
- Lucide React
- jsPDF

### Backend

- Python
- FastAPI
- Uvicorn
- Pandas
- Scikit-learn
- Joblib

### Machine Learning

- Logistic Regression
- AST-based feature extraction
- Feature engineering
- Threshold tuning
- Dual-risk classification

### Development Tools

- Git
- GitHub
- VS Code
- Jupyter Notebook

---

## 📁 Project Structure

```text
NotebookGuardian-AI/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── services/
│       ├── __init__.py
│       └── notebook_analyzer.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── ml/
│   ├── data/
│   ├── models/
│   │   ├── code_risk_model.joblib
│   │   ├── execution_risk_model.joblib
│   │   ├── notebookguardian_model.joblib
│   │   ├── dual_model_config.json
│   │   └── model_config.json
│   │
│   └── src/
│
├── docs/
│   └── screenshots/
│
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Local Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Ashutosh9-pan/NotebookGuardian-AI.git
cd NotebookGuardian-AI
```

---

### 2. Backend Setup

Create a Python virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
pip install -r backend/requirements.txt
```

Start the backend:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Backend API:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

### 3. Frontend Setup

Open a second terminal and navigate to the frontend:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Create:

```text
frontend/.env
```

Add:

```env
VITE_API_URL=http://127.0.0.1:8000/analyze
```

Start the frontend:

```powershell
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

---

## 🔐 Environment Variables

The frontend uses:

```env
VITE_API_URL=http://127.0.0.1:8000/analyze
```

For production, replace the local backend URL with the deployed API endpoint.

The `.env` file is intentionally excluded from Git using `.gitignore`.

---

## 📸 Screenshots

Screenshots of the application will be added here.

### Dashboard

![NotebookGuardian Dashboard](docs/screenshots/dashboard.png)

### Risk Analysis

![Risk Analysis Dashboard](docs/screenshots/risk-analysis.png)

### Why Flagged

![Why This Cell Is Flagged](docs/screenshots/why-flagged.png)

### Code Preview

![Code Preview](docs/screenshots/code-preview.png)

### PDF Report

![PDF Report](docs/screenshots/pdf-report.png)

---

## 🧪 Example Analysis

A notebook containing multiple Python cells can be uploaded to NotebookGuardian AI.

The system analyzes each code cell and returns information such as:

```text
Cell #35
Code Risk: 34.49%
Execution Risk: 70.49%
Risk Level: Medium
```

The dashboard allows the user to inspect the cell and understand the signals contributing to its risk classification.

---

## 📌 Model Files

The trained models are stored in:

```text
ml/models/
```

Available model files:

```text
code_risk_model.joblib
execution_risk_model.joblib
notebookguardian_model.joblib
dual_model_config.json
model_config.json
```

These files are required by the backend for notebook analysis.

---

## 🔄 Development Workflow

The project follows a development workflow consisting of:

```text
Dataset
   ↓
Feature Extraction
   ↓
Feature Analysis
   ↓
Model Training
   ↓
Model Comparison
   ↓
Cross Validation
   ↓
Threshold Tuning
   ↓
Model Saving
   ↓
FastAPI Integration
   ↓
React Dashboard
```

---

## 🚀 Future Improvements

Planned improvements may include:

- 🌐 Production deployment
- 📚 Larger and more diverse notebook datasets
- 🧠 More advanced ML models
- 🔬 Explainable AI enhancements
- 📊 Historical notebook comparison
- 👥 User accounts and saved reports
- ☁️ Cloud-based notebook analysis
- 🔗 GitHub notebook integration

---

## 👨‍💻 Author

### Ashutosh Panwar

**B.Tech CSE Graduate**

AI/ML Developer | Data Analyst | Android Developer

### Links

- GitHub: https://github.com/Ashutosh9-pan
- Portfolio: https://ashutosh-panwar-portfolio.vercel.app/

---

## 📜 License

This project is intended for educational, portfolio, and research purposes.

---

## ⭐ Support

If you find NotebookGuardian AI interesting, consider giving the repository a ⭐ on GitHub.