from pathlib import Path
import shutil
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.services.notebook_analyzer import analyze_notebook

app = FastAPI(
    title="NotebookGuardian AI API",
    description="AI-powered Jupyter notebook risk analysis API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("backend/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def root():
    return {
        "app": "NotebookGuardian AI",
        "status": "running",
        "message": "Backend API is working"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": "NotebookGuardian combined risk model"
    }


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    filename = file.filename or ""

    if not filename.lower().endswith(".ipynb"):
        raise HTTPException(
            status_code=400,
            detail="Only .ipynb Jupyter Notebook files are supported."
        )

    unique_name = f"{uuid.uuid4().hex}_{filename}"
    saved_path = UPLOAD_DIR / unique_name

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = analyze_notebook(saved_path)
        result["original_filename"] = filename

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}"
        ) from exc

    finally:
        try:
            file.file.close()
        except Exception:
            pass

        if saved_path.exists():
            saved_path.unlink()
