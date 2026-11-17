"""Internal (service-to-service) routes of the data feature. Mounted only in microservices mode."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...core.internal import require_internal_token
from .repository import QueryError, QueryTimeout
from .safety import UnsafeSQLError
from .service import DataService


class ExecuteRequest(BaseModel):
    sql: str


def build_internal_router(service: DataService, token: str) -> APIRouter:
    router = APIRouter(prefix="/internal", dependencies=[Depends(require_internal_token(token))])

    @router.get("/schema-text")
    def schema_text():
        return {"schema_text": service.schema_text(), "tables": service.table_names()}

    @router.post("/execute")
    def execute(req: ExecuteRequest):
        try:
            return service.execute(req.sql)
        except UnsafeSQLError as e:
            raise HTTPException(400, str(e)) from e
        except QueryTimeout as e:
            raise HTTPException(408, str(e)) from e
        except QueryError as e:
            raise HTTPException(422, str(e)) from e

    return router
