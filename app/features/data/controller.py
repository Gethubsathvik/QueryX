"""Data controller: public HTTP routes for schema and CSV upload."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from .repository import CSVImportError
from .service import DataService


def build_router(service: DataService) -> APIRouter:
    router = APIRouter()

    @router.get("/api/schema")
    def schema():
        return {"tables": service.schema()}

    @router.post("/api/upload")
    async def upload(file: UploadFile = File(...)):
        if not (file.filename or "").lower().endswith(".csv"):
            raise HTTPException(400, "Please upload a .csv file.")
        data = await file.read()
        try:
            return service.import_csv(file.filename, data)
        except CSVImportError as e:
            raise HTTPException(400, str(e)) from e

    return router
