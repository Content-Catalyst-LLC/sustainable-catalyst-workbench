from app.v320 import (
    ArticleRecord, ArticleNormalizeRequest, FormulaRecord, FormulaRegistryRequest,
    EmbedPlanRequest, ArticleProjectRequest, LibrarianRouteRequest,
    CitationBundleRequest, DraftPlanRequest, normalize_article,
    build_formula_registry, build_embed_plan, build_project_from_article,
    build_librarian_route, build_citation_bundle, build_draft_plan,
)


def article():
    return ArticleRecord(
        article_id="planetary-boundaries",
        wordpress_id=42,
        title="Planetary Boundaries",
        url="https://example.org/planetary-boundaries",
        topics=["sustainability", "earth systems", "sustainability"],
        citations=[{"id":"SRC-1","title":"Source","url":"https://example.org/source"}],
        formulas=[FormulaRecord(expression="F = ma", label="Force", calculator="force")],
    )


def test_normalize_article_is_hashed_and_deduplicates_topics():
    result = normalize_article(article())
    assert result["schema"] == "sc-workbench-library-article/1.0"
    assert result["content_hash"]
    assert result["topics"] == ["earth systems", "sustainability"]
    assert result["formulas"][0]["formula_id"]


def test_formula_registry_builds_hashed_records():
    result = build_formula_registry(FormulaRegistryRequest(article=article()))
    assert result["count"] == 1
    assert result["records"][0]["recordHash"]
    assert result["records"][0]["calculator"] == "force"


def test_embed_plan_builds_reviewable_shortcode():
    result = build_embed_plan(EmbedPlanRequest(article=article()))
    assert result["count"] == 1
    assert "sc_workbench_calculator_embed" in result["embeds"][0]["shortcode"]
    assert 'display="compact"' in result["embeds"][0]["shortcode"]


def test_article_project_uses_persistent_project_schema():
    result = build_project_from_article(ArticleProjectRequest(article=article()))
    project = result["project"]
    assert project["schema"] == "sc-workbench-persistent-project/1.0"
    assert project["active_studio"] == "library"
    assert project["studio_records"]["library"]["article"]["article_id"] == "planetary-boundaries"
    assert project["content_hash"]


def test_librarian_route_maps_graph_to_visualization():
    result = build_librarian_route(LibrarianRouteRequest(article=article(), question="Graph this relationship", requested_action="graph"))
    assert result["route"]["targetStudio"] == "visualization"
    assert result["route"]["routeHash"]


def test_citation_bundle_deduplicates_by_url():
    result = build_citation_bundle(CitationBundleRequest(article=article(), additional_sources=[{"title":"Duplicate","url":"https://example.org/source"}]))
    assert result["count"] == 1
    assert result["bundleHash"]


def test_draft_plan_is_human_reviewed():
    result = build_draft_plan(DraftPlanRequest(article=article(), project_id="project-1", content_markdown="# Draft"))
    assert result["draftPlan"]["reviewState"] == "human-review-required"
    assert result["draftPlan"]["visibility"] == "draft"
    assert result["draftHash"]
