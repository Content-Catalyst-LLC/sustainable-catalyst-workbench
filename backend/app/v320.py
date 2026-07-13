from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

VERSION = "3.2.0"
ARTICLE_SCHEMA = "sc-workbench-library-article/1.0"
FORMULA_SCHEMA = "sc-workbench-formula-registry/1.0"
EMBED_SCHEMA = "sc-workbench-article-embed-plan/1.0"
PROJECT_SCHEMA = "sc-workbench-article-project/1.0"
ROUTE_SCHEMA = "sc-workbench-librarian-route/1.0"
CITATION_SCHEMA = "sc-workbench-citation-bundle/1.0"
DRAFT_SCHEMA = "sc-workbench-article-draft-plan/1.0"

router = APIRouter(prefix="/v320", tags=["workbench-v320"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return clean[:96] or "record"


class FormulaRecord(BaseModel):
    formula_id: str = ""
    expression: str
    label: str = ""
    context: str = ""
    variables: dict[str, str] = Field(default_factory=dict)
    units: dict[str, str] = Field(default_factory=dict)
    calculator: str = ""
    placement: Literal["inline", "compact", "drawer", "full"] = "compact"

    @field_validator("expression")
    @classmethod
    def expression_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("expression is required")
        return value[:2000]


class ArticleRecord(BaseModel):
    article_id: str = ""
    wordpress_id: int = 0
    title: str
    url: str = ""
    excerpt: str = ""
    post_type: str = "post"
    status: str = "publish"
    topics: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    formulas: list[FormulaRecord] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title")
    @classmethod
    def title_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title is required")
        return value[:300]


class ArticleNormalizeRequest(BaseModel):
    article: ArticleRecord


class FormulaRegistryRequest(BaseModel):
    article: ArticleRecord
    existing_formula_ids: list[str] = Field(default_factory=list)


class EmbedPlanRequest(BaseModel):
    article: ArticleRecord
    formula_ids: list[str] = Field(default_factory=list)
    default_display: Literal["inline", "compact", "drawer", "full"] = "compact"


class ArticleProjectRequest(BaseModel):
    article: ArticleRecord
    project_id: str = ""
    include_formulas: bool = True
    include_citations: bool = True


class LibrarianRouteRequest(BaseModel):
    article: ArticleRecord
    question: str
    requested_action: Literal["explain", "calculate", "graph", "simulate", "validate", "build", "document"] = "calculate"


class CitationBundleRequest(BaseModel):
    article: ArticleRecord
    additional_sources: list[dict[str, Any]] = Field(default_factory=list)


class DraftPlanRequest(BaseModel):
    article: ArticleRecord
    project_id: str
    title: str = ""
    content_markdown: str
    visibility: Literal["private", "draft"] = "draft"
    evidence_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)


def normalize_article(article: ArticleRecord) -> dict[str, Any]:
    data = article.model_dump()
    data["schema"] = ARTICLE_SCHEMA
    data["article_id"] = _slug(data.get("article_id") or data.get("title") or str(data.get("wordpress_id") or "article"))
    data["post_type"] = _slug(data.get("post_type") or "post")
    data["status"] = _slug(data.get("status") or "publish")
    data["topics"] = sorted({str(item).strip()[:100] for item in data.get("topics", []) if str(item).strip()})
    normalized_formulas = []
    for index, raw in enumerate(data.get("formulas", []), start=1):
        formula = dict(raw)
        formula["formula_id"] = _slug(formula.get("formula_id") or f"{data['article_id']}-formula-{index}")
        formula["expression"] = str(formula.get("expression", "")).strip()
        formula["label"] = str(formula.get("label", "")).strip()[:200]
        formula["calculator"] = _slug(formula.get("calculator", "")) if formula.get("calculator") else ""
        normalized_formulas.append(formula)
    data["formulas"] = normalized_formulas
    data["normalized_at"] = _now()
    unhashed = dict(data)
    data["content_hash"] = _hash(unhashed)
    return data


def build_formula_registry(request: FormulaRegistryRequest) -> dict[str, Any]:
    article = normalize_article(request.article)
    existing = {_slug(item) for item in request.existing_formula_ids}
    records = []
    duplicates = []
    for formula in article["formulas"]:
        record = {
            "schema": FORMULA_SCHEMA,
            "version": VERSION,
            "formulaId": formula["formula_id"],
            "articleId": article["article_id"],
            "articleTitle": article["title"],
            "expression": formula["expression"],
            "label": formula.get("label", ""),
            "context": formula.get("context", ""),
            "variables": formula.get("variables", {}),
            "units": formula.get("units", {}),
            "calculator": formula.get("calculator", ""),
            "placement": formula.get("placement", "compact"),
        }
        record["recordHash"] = _hash(record)
        if record["formulaId"] in existing:
            duplicates.append(record["formulaId"])
        records.append(record)
    return {
        "ok": True,
        "schema": FORMULA_SCHEMA,
        "version": VERSION,
        "articleId": article["article_id"],
        "records": records,
        "count": len(records),
        "duplicates": sorted(duplicates),
        "registryHash": _hash(records),
    }


def build_embed_plan(request: EmbedPlanRequest) -> dict[str, Any]:
    article = normalize_article(request.article)
    selected = set(request.formula_ids)
    if not selected:
        selected = {formula["formula_id"] for formula in article["formulas"]}
    embeds = []
    for formula in article["formulas"]:
        if formula["formula_id"] not in selected:
            continue
        calculator = formula.get("calculator") or "symbolic-math"
        display = formula.get("placement") or request.default_display
        shortcode = (
            f'[sc_workbench_calculator_embed article="{article["article_id"]}" '
            f'formula="{formula["formula_id"]}" calculator="{calculator}" display="{display}"]'
        )
        embed = {
            "formulaId": formula["formula_id"],
            "calculator": calculator,
            "display": display,
            "shortcode": shortcode,
            "placementHint": f'Place after the paragraph explaining {formula.get("label") or formula["expression"][:80]}',
        }
        embed["embedHash"] = _hash(embed)
        embeds.append(embed)
    return {
        "ok": True,
        "schema": EMBED_SCHEMA,
        "version": VERSION,
        "articleId": article["article_id"],
        "embeds": embeds,
        "count": len(embeds),
        "planHash": _hash(embeds),
    }


def build_project_from_article(request: ArticleProjectRequest) -> dict[str, Any]:
    article = normalize_article(request.article)
    project_id = _slug(request.project_id or f"article-{article['article_id']}")
    record = {
        "schema": "sc-workbench-persistent-project/1.0",
        "project_id": project_id,
        "wordpress_id": 0,
        "title": f"Article project · {article['title']}",
        "description": article.get("excerpt", ""),
        "status": "draft",
        "owner_id": "",
        "storage_mode": "browser",
        "tags": sorted(set(article.get("topics", []) + ["knowledge-library", "article-integration"])),
        "pinned": False,
        "created_at": _now(),
        "updated_at": _now(),
        "local_revision": 0,
        "server_revision": 0,
        "active_studio": "library",
        "studio_records": {
            "library": {
                "schema": PROJECT_SCHEMA,
                "article": article,
                "formulaRegistry": article["formulas"] if request.include_formulas else [],
                "citations": article["citations"] if request.include_citations else [],
            }
        },
        "evidence_ids": [str(item.get("id") or item.get("citation_id") or "").strip() for item in article["citations"] if str(item.get("id") or item.get("citation_id") or "").strip()],
        "artifact_ids": [],
        "metadata": {"sourceArticleId": article["article_id"], "sourceArticleUrl": article.get("url", "")},
        "content_hash": "",
    }
    unhashed = dict(record)
    unhashed.pop("content_hash", None)
    record["content_hash"] = _hash(unhashed)
    return {"ok": True, "schema": PROJECT_SCHEMA, "version": VERSION, "project": record, "projectHash": record["content_hash"]}


def build_librarian_route(request: LibrarianRouteRequest) -> dict[str, Any]:
    article = normalize_article(request.article)
    question = request.question.strip()
    if not question:
        raise ValueError("question is required")
    action_map = {
        "explain": "research",
        "calculate": "unified",
        "graph": "visualization",
        "simulate": "simulation",
        "validate": "documentation",
        "build": "embedded",
        "document": "documentation",
    }
    target = action_map[request.requested_action]
    packet = {
        "schema": ROUTE_SCHEMA,
        "version": VERSION,
        "createdAt": _now(),
        "articleId": article["article_id"],
        "articleTitle": article["title"],
        "articleUrl": article.get("url", ""),
        "question": question,
        "requestedAction": request.requested_action,
        "targetStudio": target,
        "workbenchHash": f"#workbench-studio-{target}",
        "formulaIds": [formula["formula_id"] for formula in article["formulas"]],
        "citationCount": len(article["citations"]),
        "scopeBoundary": "Route only within Sustainable Catalyst topics, article evidence, and registered Workbench tools.",
    }
    packet["routeHash"] = _hash(packet)
    return {"ok": True, "schema": ROUTE_SCHEMA, "version": VERSION, "route": packet, "routeHash": packet["routeHash"]}


def build_citation_bundle(request: CitationBundleRequest) -> dict[str, Any]:
    article = normalize_article(request.article)
    sources = list(article["citations"]) + list(request.additional_sources)
    normalized = []
    seen = set()
    for index, source in enumerate(sources, start=1):
        item = dict(source)
        key = str(item.get("url") or item.get("doi") or item.get("title") or index).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        citation_id = _slug(item.get("id") or item.get("citation_id") or f"{article['article_id']}-source-{index}")
        record = {
            "citationId": citation_id,
            "title": str(item.get("title", "")).strip(),
            "url": str(item.get("url", "")).strip(),
            "doi": str(item.get("doi", "")).strip(),
            "publisher": str(item.get("publisher", "")).strip(),
            "published": str(item.get("published", "")).strip(),
            "accessed": str(item.get("accessed", "")).strip(),
            "notes": str(item.get("notes", "")).strip(),
        }
        record["citationHash"] = _hash(record)
        normalized.append(record)
    bundle = {"schema": CITATION_SCHEMA, "version": VERSION, "articleId": article["article_id"], "generatedAt": _now(), "citations": normalized}
    bundle["bundleHash"] = _hash(bundle)
    return {"ok": True, "schema": CITATION_SCHEMA, "version": VERSION, "bundle": bundle, "bundleHash": bundle["bundleHash"], "count": len(normalized)}


def build_draft_plan(request: DraftPlanRequest) -> dict[str, Any]:
    article = normalize_article(request.article)
    title = request.title.strip() or f"Workbench return · {article['title']}"
    plan = {
        "schema": DRAFT_SCHEMA,
        "version": VERSION,
        "createdAt": _now(),
        "sourceArticleId": article["article_id"],
        "sourceArticleTitle": article["title"],
        "sourceArticleUrl": article.get("url", ""),
        "projectId": _slug(request.project_id),
        "title": title[:300],
        "contentMarkdown": request.content_markdown,
        "visibility": request.visibility,
        "evidenceIds": sorted(set(request.evidence_ids)),
        "artifactIds": sorted(set(request.artifact_ids)),
        "reviewState": "human-review-required",
        "publicationBoundary": "Create a private or draft record only. Human review is required before publication.",
    }
    plan["draftHash"] = _hash(plan)
    return {"ok": True, "schema": DRAFT_SCHEMA, "version": VERSION, "draftPlan": plan, "draftHash": plan["draftHash"]}


@router.get("/status")
def status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "schema": ARTICLE_SCHEMA,
        "capabilities": [
            "article-normalization",
            "formula-registry",
            "calculator-embed-planning",
            "project-from-article",
            "research-librarian-routing",
            "citation-bundles",
            "private-draft-return-planning",
        ],
    }


@router.post("/article/normalize")
def article_normalize(request: ArticleNormalizeRequest) -> dict[str, Any]:
    article = normalize_article(request.article)
    return {"ok": True, "schema": ARTICLE_SCHEMA, "version": VERSION, "article": article, "articleHash": article["content_hash"]}


@router.post("/formula/registry")
def formula_registry(request: FormulaRegistryRequest) -> dict[str, Any]:
    return build_formula_registry(request)


@router.post("/embed/plan")
def embed_plan(request: EmbedPlanRequest) -> dict[str, Any]:
    return build_embed_plan(request)


@router.post("/project/from-article")
def project_from_article(request: ArticleProjectRequest) -> dict[str, Any]:
    return build_project_from_article(request)


@router.post("/librarian/route")
def librarian_route(request: LibrarianRouteRequest) -> dict[str, Any]:
    return build_librarian_route(request)


@router.post("/citation/bundle")
def citation_bundle(request: CitationBundleRequest) -> dict[str, Any]:
    return build_citation_bundle(request)


@router.post("/draft/plan")
def draft_plan(request: DraftPlanRequest) -> dict[str, Any]:
    return build_draft_plan(request)
