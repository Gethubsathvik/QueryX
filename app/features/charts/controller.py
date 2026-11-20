"""Charts controller: the catalog and the chart-building endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .errors import ChartError
from .service import ChartService


class ChartRequest(BaseModel):
    columns: list[str] = Field(min_length=1, max_length=200)
    rows: list[list] = Field(max_length=5000)
    chart: str = Field(max_length=40)
    mapping: dict | None = None
    options: dict | None = None


class CompatibleRequest(BaseModel):
    columns: list[str] = Field(min_length=1, max_length=200)
    rows: list[list] = Field(max_length=5000)


def build_router(service: ChartService) -> APIRouter:
    router = APIRouter()

    @router.get("/api/charts")
    def catalog():
        return service.catalog()

    @router.post("/api/charts/compatible")
    def compatible(req: CompatibleRequest):
        return {"compatible": service.compatible(req.columns, req.rows)}

    @router.post("/api/chart")
    def chart(req: ChartRequest):
        try:
            return service.build(
                req.columns, req.rows, req.chart, req.mapping, req.options
            )
        except ChartError as e:
            raise HTTPException(422, str(e)) from e

    return router
