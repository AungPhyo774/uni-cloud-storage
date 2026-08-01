from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path


app = FastAPI(
    title="Distributed Cloud Storage - Storage Service"
)


STORAGE_DIR = Path("storage")

STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


@app.get("/")
def home():
    return {
        "message": "Storage Service is running"
    }


@app.post("/storage/upload")
async def upload_file(
    file: UploadFile = File(...)
):
    file_path = STORAGE_DIR / file.filename

    try:
        with open(file_path, "wb") as buffer:

            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to save file"
        )

    return {
        "message": "File stored successfully",
        "file_name": file.filename,
        "file_path": str(file_path)
    }