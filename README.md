# ECD Intelligence Platform

Enterprise AI intelligence platform for organisations operating in the Early Childhood Development (ECD) ecosystem.

The platform is being built as a **production-oriented, multi-organisation intelligence system** rather than a single-purpose chatbot. It will allow an organisation to connect its own operational data, documents, knowledge sources, and external tools, then ask natural-language questions and receive grounded, traceable answers.

## Product vision

The platform should ultimately provide a plug-and-play intelligence layer for organisations such as ECD networks and NGOs. A customer should be able to bring its own data and knowledge sources without requiring a separate codebase for every organisation.

The core architecture will combine:

- PostgreSQL and structured organisational data
- Safe SQL analytics
- LangGraph agent orchestration
- LLM-based reasoning and text-to-SQL
- Organisation-scoped document retrieval
- Research Agent orchestration across SQL, internal knowledge, and external knowledge
- Web and external knowledge retrieval
- MCP/tool integrations
- Multi-organisation / tenant isolation
- Evidence, citations, and provenance
- Evaluation and regression testing
- Security, governance and auditability
- Observability and production deployment

---

# Implementation status

Legend:

- ✅ **Shipped** — implemented and tested
- 🚧 **In progress** — currently being developed
- ⬜ **Planned** — not implemented yet

## Foundation — shipped capabilities

| Component | Status |
|---|---|
| Python/uv development environment | ✅ Shipped |
| PostgreSQL database | ✅ Shipped |
| SQLAlchemy database layer | ✅ Shipped |
| Core ECD/organisation schema | ✅ Shipped |
| Seed data | ✅ Shipped |
| Read-only SQL execution tool | ✅ Shipped |
| SQL safety validation | ✅ Shipped |
| Organisation-aware request context | ✅ Shipped |
| Organisation-scoped analytics | ✅ Shipped |
| LangGraph analytics workflow | ✅ Shipped |
| FastAPI application | ✅ Shipped |
| `/health` endpoint | ✅ Shipped |
| `/api/v1` API structure | ✅ Shipped |
| `/api/v1/agent/query` endpoint | ✅ Shipped |
| API response schemas | ✅ Shipped |
| Document model | ✅ Shipped |
| Document chunk model | ✅ Shipped |
| Deterministic document chunking | ✅ Shipped |
| Embedding service | ✅ Shipped |
| Dynamic embedding-dimension discovery | ✅ Shipped |
| Embedding provider abstraction | ✅ Shipped |
| pgvector storage | ✅ Shipped |
| Organisation-scoped vector retrieval | ✅ Shipped |
| Vector similarity search | ✅ Shipped |
| Embedding deletion | ✅ Shipped |
| Automated service/API/tool tests | ✅ Shipped |
| GitHub version control | ✅ Shipped |

**Current verified baseline: 135 automated tests passing.**

The foundation is the baseline that all subsequent phases must preserve. New capabilities must be added incrementally and must not introduce hard-coded embedding dimensions or other provider-specific assumptions into the application architecture.

---

# Roadmap

## Phase 1 — Enterprise foundation

**Status: ✅ Shipped**

Goal: establish the database, organisation model, safe SQL execution, application structure, and initial LangGraph analytics workflow.

### Completed work

- [x] Python/uv project environment
- [x] PostgreSQL
- [x] SQLAlchemy
- [x] Core organisation/ECD schema
- [x] Seed data
- [x] Read-only SQL execution
- [x] SQL safety validation
- [x] Initial LangGraph workflow
- [x] FastAPI application
- [x] Health endpoint
- [x] Initial agent endpoint
- [x] Automated tests

---

## Phase 2 — Production API and multi-organisation architecture

**Status: ✅ Shipped**

Goal: turn the initial analytics system into a properly scoped enterprise platform.

### Completed work

- [x] Organisation model and relationships
- [x] Organisation-aware request context
- [x] Organisation scoping at the query layer
- [x] Cross-organisation data-leakage protections
- [x] Organisation management/read API
- [x] `/api/v1` API versioning
- [x] Formal request/response contracts
- [x] Tenant-isolation tests
- [x] Organisation service tests
- [x] Removal of obsolete legacy API code

### Exit criteria

- Every analytics request can be scoped to an organisation.
- A nonexistent organisation is rejected before analytics execution.
- Existing foundation tests remain green.
- API contracts are versioned and stable.

---

## Phase 3 — Document and vector retrieval foundation

**Status: ✅ Shipped**

Goal: establish the organisation-scoped unstructured knowledge layer that the Research Agent will use.

### Completed work

- [x] Document data model
- [x] Document chunk data model
- [x] Organisation/document ownership relationships
- [x] Deterministic chunking foundation
- [x] Embedding service
- [x] Embedding model abstraction
- [x] Runtime embedding-dimension discovery
- [x] No hard-coded application embedding dimension
- [x] pgvector integration
- [x] Store chunk embeddings
- [x] Delete chunk embeddings
- [x] Organisation-filtered semantic search
- [x] Document provenance fields
- [x] Vector service tests
- [x] Embedding service tests

### Architectural rule

The application does **not** assume that embeddings are 384, 768, or any other fixed dimension. The active embedding provider/model determines the vector dimension at runtime. The retrieval layer accepts the discovered embedding and PostgreSQL/pgvector enforces compatibility with the configured vector storage.

### Verification checkpoint

```text
107 passed
```

---

## Phase 4 — Research Agent

**Status: 🚧 Current major phase**

Goal: build a real research-oriented LangGraph agent that can decide what evidence it needs, retrieve that evidence from the appropriate sources, and produce a grounded answer with provenance.

This replaces the previous roadmap concept of **External RAG**. External knowledge is now a capability of the Research Agent rather than a separate isolated phase.

The Research Agent is not simply a vector-search wrapper. It is a controlled reasoning workflow that can combine multiple evidence sources.

### Target architecture

```text
                              User Question
                                   |
                                   v
                         +-----------------------+
                         |    Research Agent     |
                         |       LangGraph       |
                         +-----------+-----------+
                                     |
                                     v
                              Question Router
                                     |
                +--------------------+--------------------+
                |                    |                    |
                v                    v                    v
          SQL Research       Internal Knowledge      External Research
                |                    |                    |
                v                    v                    v
          PostgreSQL            pgvector/KB           Web/APIs
                |                    |                    |
                +--------------------+--------------------+
                                     |
                                     v
                            Evidence Aggregation
                                     |
                                     v
                           Evidence-aware Synthesis
                                     |
                                     v
                         Grounded Answer + Sources
```

### RAG/research sources

- [x] Structured organisational data through SQL
- [x] Organisation-owned documents through vector retrieval
- [x] External knowledge sources
- [x] Live web research
- [ ] External APIs where appropriate
- [ ] Customer-provided knowledge sources

### RAG-1 — Research Agent state and graph

- [x] Define `ResearchState`
- [x] Define research evidence schema
- [x] Define source/provenance schema
- [x] Define graph nodes and transitions
- [x] Define terminal answer state
- [x] Add deterministic graph tests
- [x] Preserve existing analytics workflow

### RAG-2 — Research question routing

- [x] Classify question requirements
- [x] Detect SQL-required questions
- [x] Detect internal-knowledge questions
- [x] Detect external-research questions
- [x] Detect multi-source questions
- [x] Support direct-answer path where retrieval is unnecessary
- [x] Add routing tests

### RAG-3 — Internal knowledge retrieval tool

- [x] Wrap vector search as an agent tool
- [x] Generate query embeddings through the embedding service
- [x] Preserve runtime embedding dimensions
- [x] Enforce organisation filtering
- [x] Return document/chunk metadata
- [x] Return similarity scores
- [x] Return provenance
- [x] Add retrieval tool tests

### RAG-4 — SQL research tool

- [x] Expose safe SQL analytics to the Research Agent
- [x] Preserve organisation validation
- [x] Preserve read-only SQL enforcement
- [x] Return structured evidence
- [x] Include query/source metadata
- [x] Prevent unrestricted database access
- [x] Add agent-to-SQL tests

### RAG-5 — External research tool

- [x] Define external research interface
- [x] Add web-search abstraction
- [x] Retrieve external evidence
- [x] Capture source URL/title metadata
- [x] Handle timeouts and failures
- [x] Prevent external results from bypassing organisation security
- [x] Add external research tests with mocked providers

### RAG-6 — Evidence aggregation

- [x] Combine SQL evidence
- [x] Combine internal document evidence
- [x] Combine external research evidence
- [x] Preserve source identity
- [x] Preserve organisation identity
- [x] Detect conflicting evidence
- [x] Rank/select useful evidence
- [x] Remove duplicate evidence
- [x] Add evidence aggregation tests

### RAG-7 — Grounded answer synthesis

- [x] Build synthesis prompt
- [x] Pass only selected evidence to the answer model
- [x] Require evidence-grounded claims
- [x] Generate citations/source references
- [x] Distinguish organisational facts from external facts
- [x] Handle insufficient evidence
- [x] Add hallucination/grounding tests

### RAG-8 — Research loop

The agent should be able to recognise when the first retrieval attempt is insufficient and perform another controlled research step.

- [ ] Evidence sufficiency evaluation
- [ ] Follow-up retrieval
- [ ] Query refinement
- [ ] Maximum research-step limit
- [ ] Failure/recovery path
- [ ] Termination condition
- [ ] Research trajectory tests

### RAG-9 — Research Agent API

- [ ] Add `/api/v1/research` endpoint
- [ ] Define request schema
- [ ] Define response schema
- [ ] Return answer and evidence metadata
- [ ] Return citations
- [ ] Preserve organisation scope
- [ ] Add API integration tests

### Research Agent exit criteria

The phase is complete when the system can receive a question such as:

```text
How many franchisees are operating in Gauteng, and what does our latest
ECD programme documentation say about the factors affecting programme quality?
```

and deliberately determine that it requires **both structured SQL evidence and internal document retrieval**, execute both safely, combine the evidence, and return a grounded answer with provenance.

A second class of question should be able to trigger external research when required, while keeping organisational data and external evidence clearly separated.

---

## Phase 5 — LLM-powered analytics and reasoning

**Status: ⬜ Planned**

Replace the remaining deterministic analytics planning with controlled LLM reasoning while retaining all existing safety boundaries.

### Work items

- [ ] LLM provider abstraction
- [ ] Schema-aware text-to-SQL generation
- [ ] Intent classification
- [ ] SQL generation prompt architecture
- [ ] SQL validation before execution
- [ ] SQL query repair loop
- [ ] Result interpretation
- [ ] Natural-language answer generation
- [ ] Model fallback strategy
- [ ] LLM evaluation dataset
- [ ] Generated-SQL regression tests
- [ ] Cost and latency tracking

### Important principle

The LLM must **not** receive unrestricted database execution privileges. Generated SQL must pass the existing safety layer and database permissions before execution.

---

## Phase 6 — MCP and enterprise tool ecosystem

**Status: ⬜ Planned**

Introduce standardised tool interfaces for external systems.

### Work items

- [ ] MCP architecture
- [ ] MCP server/client integration where appropriate
- [ ] Tool discovery
- [ ] Tool schemas
- [ ] Tool permissions
- [ ] Tool execution policies
- [ ] Timeouts and retries
- [ ] Tool audit logging
- [ ] External enterprise connectors

The Research Agent should use tools deliberately and observably rather than simply generating text.

---

## Phase 7 — Advanced multi-agent architecture

**Status: ⬜ Planned**

Evolve the Research Agent into a controlled multi-agent intelligence system only where demonstrated requirements justify the additional complexity.

### Planned components

- [ ] Supervisor/router
- [ ] Research Agent
- [ ] Analytics agent
- [ ] SQL specialist
- [ ] Internal knowledge retrieval specialist
- [ ] Web research specialist
- [ ] External-tool specialist
- [ ] Synthesis agent
- [ ] Shared state
- [ ] Memory strategy where appropriate
- [ ] Human approval points for sensitive actions
- [ ] Feedback loops
- [ ] Failure/recovery paths

The system should qualify as an agent architecture because it can select tools/routes, maintain state, execute actions, observe results, and continue or terminate based on those results.

---

## Phase 8 — Evaluation and reliability

**Status: ⬜ Planned**

Evaluation is part of the product architecture, not a final-stage activity.

### Work items

- [ ] Golden question dataset
- [ ] SQL correctness evaluation
- [ ] Routing accuracy evaluation
- [ ] Retrieval precision/recall evaluation
- [ ] Evidence quality evaluation
- [ ] Answer quality evaluation
- [ ] Citation/provenance evaluation
- [ ] Hallucination tests
- [ ] Research trajectory evaluation
- [ ] Agent tool-selection evaluation
- [ ] Latency benchmarks
- [ ] Token/cost benchmarks
- [ ] Automated regression suite
- [ ] Production acceptance thresholds

Every major architectural change should be evaluated against a known baseline.

---

## Phase 9 — Security and governance

**Status: ⬜ Planned**

### Work items

- [ ] Authentication
- [ ] RBAC
- [ ] Organisation/tenant isolation
- [ ] Database-level read-only permissions
- [ ] Secrets management
- [ ] Audit logs
- [ ] PII handling
- [ ] Data retention policy
- [ ] Prompt-injection protections
- [ ] Tool authorization
- [ ] Input/output validation
- [ ] External-source trust boundaries
- [ ] Security testing

Security controls must exist at multiple layers; prompt instructions alone are not considered a security boundary.

---

## Phase 10 — Observability and production infrastructure

**Status: ⬜ Planned**

### Work items

- [ ] Structured application logging
- [ ] Agent execution tracing
- [ ] Research trajectory tracing
- [ ] Metrics
- [ ] Request latency monitoring
- [ ] SQL execution monitoring
- [ ] Retrieval monitoring
- [ ] External research monitoring
- [ ] Token/cost monitoring
- [ ] Error tracking
- [ ] Retry policies
- [ ] Timeouts/circuit breakers
- [ ] Health/readiness checks
- [ ] CI/CD
- [ ] Containerisation
- [ ] Production deployment

---

## Phase 11 — Plug-and-play customer architecture

**Status: ⬜ Planned**

This is a major product milestone.

The platform must support a new organisation without copying and rewriting the application.

### Work items

- [ ] Customer onboarding flow
- [ ] Organisation configuration
- [ ] Customer-specific schemas/connectors
- [ ] Customer-specific document collections
- [ ] Customer-specific tools
- [ ] Customer-specific permissions
- [ ] Configurable ingestion pipelines
- [ ] Configurable retrieval policies
- [ ] Data-source registration
- [ ] Organisation-level agent configuration
- [ ] Customer isolation tests

### Target architecture

```text
                    ECD Intelligence Platform
                              |
                    +---------+---------+
                    |   Research Agent  |
                    +---------+---------+
                              |
        +---------------------+---------------------+
        |                     |                     |
      SQL/RDB          Internal Knowledge      External Research
        |                     |                     |
   Customer DB          Customer KBs          Web/APIs
        |                     |                     |
        +---------------------+---------------------+
                              |
                       Evidence Layer
                              |
                       Answer Synthesis
                              |
                    Grounded enterprise answer
```

---

## Phase 12 — Intelligence product layer

**Status: ⬜ Planned**

Move from question answering toward proactive organisational intelligence.

### Planned capabilities

- [ ] Conversational analytics
- [ ] Executive dashboards
- [ ] Automated reporting
- [ ] Anomaly detection
- [ ] Trend detection
- [ ] Forecasting
- [ ] Recommendations
- [ ] Proactive alerts
- [ ] Operational intelligence
- [ ] Decision-support workflows
- [ ] Scheduled intelligence reports

---

# Current architecture

The current shipped path combines organisation-scoped analytics with the unstructured knowledge foundation:

```text
User
  |
  v
FastAPI /api/v1
  |
  v
Organisation validation
  |
  +----------------------+
  |                      |
  v                      v
Analytics Workflow    Document/Vector Layer
(LangGraph)           (pgvector)
  |                      |
  v                      v
PostgreSQL          Organisation KB
```

The next architecture increment introduces the Research Agent above these capabilities:

```text
                         /api/v1/research
                                |
                        Organisation scope
                                |
                                v
                       +------------------+
                       |  Research Agent  |
                       |    LangGraph     |
                       +--------+---------+
                                |
             +------------------+------------------+
             |                  |                  |
             v                  v                  v
            SQL          Internal Knowledge    External Research
             |                  |                  |
        PostgreSQL          pgvector             Web/APIs
             |                  |                  |
             +------------------+------------------+
                                |
                                v
                         Evidence Aggregation
                                |
                                v
                        Grounded Synthesis
                                |
                                v
                         Answer + Citations
```

The Research Agent should be implemented incrementally. We should not introduce multiple agents, MCP, reranking, memory, or external services merely for architectural appearance. Each component must solve a demonstrated requirement and have tests/evaluation around it.

---

# Development and tracking rules

These rules are part of the project workflow.

1. **GitHub is the source of truth.**
2. Before any major extension, inspect the current GitHub repository and relevant files.
3. Do not assume an earlier local version is still authoritative.
4. Every meaningful completed change must be committed and pushed to `main` unless we deliberately establish a branch/PR workflow.
5. Run the complete test suite before committing.
6. Do not break existing functionality while adding new phases.
7. Update this README whenever a roadmap item moves from planned to in progress or shipped.
8. Add tests with new functionality.
9. Keep security boundaries explicit and enforce them in code/database permissions, not only in prompts.
10. Prefer small, verifiable increments over large rewrites.
11. Do not introduce provider-specific assumptions such as fixed embedding dimensions into generic application logic.
12. After every completed increment, verify local `main` and GitHub `main` are synchronised before starting the next major increment.
13. Follow the project loop: **Build → Test → Demonstrate → Commit → Push → Update tracking → Move to next increment.**
14. Preserve the latest verified test count as the regression baseline.

---

# Current verification baseline

Latest verified local checkpoint:

```text
107 passed
```

The embedding/vector foundation has been verified with the full test suite. The embedding service dynamically discovers the active model's dimension, while vector storage and retrieval do not hard-code an embedding size in application code.

The organisation-scoped API has been manually verified with:

```text
POST /api/v1/agent/query
{
  "question": "How many franchisees are there?",
  "organisation_id": 1
}
```

A nonexistent organisation is rejected before analytics execution:

```text
POST /api/v1/agent/query
{
  "question": "How many franchisees are there?",
  "organisation_id": 999999
}
```

with an explicit organisation-not-found error.

---

# Project tracking

## Completed

- ✅ Enterprise foundation
- ✅ Production API and multi-organisation architecture
- ✅ Document/chunk foundation
- ✅ Dynamic embedding service
- ✅ pgvector storage
- ✅ Organisation-scoped semantic retrieval
- ✅ Vector and embedding service test coverage
- ✅ Full regression suite: **135 passed**

## Current

- 🚧 **Phase 4 — Research Agent**
- ✅ RAG-1: Research Agent state and LangGraph graph
- ✅ RAG-2: Question routing
- ✅ RAG-3: Internal knowledge retrieval tool
- ✅ RAG-4: SQL research tool
- ✅ RAG-5: External research tool
- ✅ RAG-6: Evidence aggregation
- ✅ RAG-7: Grounded answer synthesis
- ⬜ RAG-8: Controlled research loop
- ⬜ RAG-9: Research Agent API

## Next checkpoint

The next implementation checkpoint is **RAG-8 — Controlled research loop**.

RAG-5 through RAG-7 add controlled external research, tenant-safe evidence aggregation, and deterministic citation-backed synthesis. RAG-8 will add bounded follow-up retrieval and evidence-sufficiency evaluation.

### RAG-1 acceptance criteria

- [x] `ResearchState` is defined
- [x] Evidence/provenance structures are defined
- [x] LangGraph research graph exists
- [x] Initial routing node exists
- [x] Graph can terminate cleanly
- [x] Existing analytics workflow remains unchanged
- [x] Research Agent unit tests are added
- [x] Full test suite remains green
- [x] README tracking is updated
- [x] Changes are committed
- [x] Changes are pushed to GitHub

---

# Repository

GitHub: `james00junior/ECD-Intelligence-Platform`

The repository history is the authoritative record of implementation progress. This README is the authoritative roadmap and feature-tracking document.
