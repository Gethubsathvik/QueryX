"""Ask controller: HTTP routes and the mapping from domain errors to status codes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...core.errors import UpstreamError
from ..data.repository import QueryError, QueryTimeout
from ..data.safety import UnsafeSQLError
from .generators import EXAMPLES, GenerationError, NoAnswer
from .schemas import AskRequest, AskResponse, SqlRequest
from .service import AskService


def build_router(service: AskService) -> APIRouter:
    router = APIRouter()

    @router.get("/api/examples")
    def examples():
        return {"examples": EXAMPLES, "engine": service.generator.name}

    @router.post("/api/ask", response_model=AskResponse)
    def ask(req: AskRequest):
        try:
            return service.ask(req.question)
        except NoAnswer as e:
            raise HTTPException(422, str(e)) from e
        except GenerationError as e:
            raise HTTPException(502, str(e)) from e
        except UnsafeSQLError as e:
            raise HTTPException(400, f"Blocked unsafe SQL: {e}") from e
        except QueryTimeout as e:
            raise HTTPException(408, f"Query timed out: {e}") from e
        except QueryError as e:
            raise HTTPException(422, str(e)) from e
        except UpstreamError as e:
            raise HTTPException(503, str(e)) from e

    @router.post("/api/sql", response_model=AskResponse)
    def run_sql(req: SqlRequest):
        try:
            return service.run_sql(req.sql)
        except NoAnswer as e:
            raise HTTPException(422, str(e)) from e
        except UnsafeSQLError as e:
            raise HTTPException(400, f"Blocked unsafe SQL: {e}") from e
        except QueryTimeout as e:
            raise HTTPException(408, f"Query timed out: {e}") from e
        except QueryError as e:
            raise HTTPException(422, str(e)) from e
        except UpstreamError as e:
            raise HTTPException(503, str(e)) from e

    return router
