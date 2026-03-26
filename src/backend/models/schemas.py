import re
from pydantic import BaseModel, field_validator


class QueryRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def clean(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("question can't be empty")
        if len(v) > 500:
            raise ValueError("max 500 chars")
        # strip non-printable chars that could confuse the LLM
        return "".join(c for c in v if c.isprintable())


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    properties: dict[str, str | int | float | None]


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    links: list[GraphEdge]


class QueryResponse(BaseModel):
    answer: str
    sql: str | None = None
    rows: list[dict] = []
    on_topic: bool = True


class StatusService(BaseModel):
    name: str
    ok: bool
    latency_ms: float


class StatusResponse(BaseModel):
    backend: StatusService
    database: StatusService
    llm: StatusService


# node ID validation pattern — matches so_740506, del_80737721, etc.
NODE_ID_PATTERN = re.compile(r"^[a-z]+_[a-zA-Z0-9]+$")
