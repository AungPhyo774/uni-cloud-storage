import hashlib

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path


app = FastAPI(
    title="Distributed Cloud Storage - Storage Service Node 3"
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


@app.get("/storage/download/{file_name}")
def download_file(file_name: str):

    file_path = STORAGE_DIR / file_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    return FileResponse(
        path=file_path,
        filename=file_name
    )

@app.delete("/storage/delete/{file_name}")
def delete_file(file_name: str):

    file_path = STORAGE_DIR / file_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    file_path.unlink()

    return {
        "message": "File deleted successfully",
        "file_name": file_name
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }

@app.get("/storage/check/{file_name}")
def check_file(file_name: str):
    file_path = STORAGE_DIR / file_name
    return {
        "file_name": file_name,
        "exists": file_path.exists()
    }


@app.post("/storage/restore/{file_name}")
async def restore_file(
    file_name: str,
    file: UploadFile = File(...)
):

    file_path = STORAGE_DIR / file_name

    try:

        with open(file_path, "wb") as buffer:

            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Failed to restore file"
        )

    return {
        "message": "File restored successfully",
        "file_name": file_name
    }


@app.get("/storage/checksum/{file_name}")
def get_file_checksum(file_name: str):

    file_path = STORAGE_DIR / file_name

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while chunk := file.read(1024 * 1024):

            sha256.update(chunk)

    return {
        "file_name": file_name,
        "checksum": sha256.hexdigest()
    }