# Sustainable Catalyst Workbench Implementation Plan

## v0.1.0 purpose

This release is a foundation package. It proves the Workbench architecture without exposing a general-purpose AI chatbot.

The core rule is:

> Sustainable Catalyst AI is site-scoped. It answers only within the Sustainable Catalyst knowledge map and routes users to articles, research paths, repositories, and Workbench tools.

## Build order

### Phase 1 — WordPress shell

- Install plugin.
- Set backend API URL.
- Add `/workbench/` page.
- Add `[sc_workbench]` to the page.
- Add `[sc_workbench_ai mode="library-guide"]` to the Research Library.
- Add topic-specific shortcodes to article maps.

### Phase 2 — Backend foundation

- Run FastAPI locally.
- Confirm `/health`, `/tools`, `/research/topics`, and `/ai/ask-library` endpoints.
- Test starter deterministic tools.
- Deploy backend to a private server or managed container.

### Phase 3 — Research Library indexing

Create an indexer that reads:

- WordPress pages
- article maps
- article excerpts
- references
- tool registry
- GitHub repository metadata

Store in PostgreSQL with pgvector-ready fields:

```sql
CREATE TABLE sc_research_documents (
  id UUID PRIMARY KEY,
  source_type TEXT NOT NULL,
  title TEXT NOT NULL,
  url TEXT,
  topic_id TEXT,
  body TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  embedding VECTOR(1536),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

### Phase 4 — AI enablement

Only enable live AI after retrieval is working.

Required controls:

- Scope gate before generation.
- Retrieval before answer.
- Refusal/redirect for out-of-scope requests.
- No general chatbot language such as "ask me anything."
- Clear limitations for legal, medical, financial, clinical, or compliance topics.

### Phase 5 — Advanced engines

Add language specialists only when needed:

- R for statistics, psychometrics, behavioral research, econometrics.
- C++ for performance-heavy simulation and graph kernels.
- Haskell for formal logic, typed rule systems, and governance validation.
- Julia for scientific simulation and differential equations.
