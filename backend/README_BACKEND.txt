NotebookGuardian AI Backend

Place these files inside:
E:\project\NotebookGuardian-AI\backend

Expected structure:

backend/
├── main.py
├── requirements.txt
├── README_BACKEND.txt
└── services/
    ├── __init__.py
    └── notebook_analyzer.py

Run from the PROJECT ROOT:

uvicorn backend.main:app --reload

Then open:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

Important:
The trained model must already exist at:
ml/models/notebookguardian_model.joblib

And config at:
ml/models/model_config.json
