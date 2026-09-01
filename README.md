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
- External RAG over organisational documents
- Web and external knowledge retrieval
- MCP/tool integrations
- Multi-organisation / tenant isolation
- Evaluation and regression testing
- Security, governance and auditability
- Observability and production deployment

---

# Implementation status

Legend:

- ✅ **Shipped** — implemented and tested
- 🚧 **In progress** — currently being developed
- ⬜ **Planned** — not implemented yet

## Phase 1 — Enterprise foundation

| Component | Status |
|---|---|
| Python/uv development environment | ✅ Shipped |
| PostgreSQL database | ✅ Shipped |
| SQLAlchemy database layer | ✅ Shipped |
| Core ECD/organisation schema | ✅ Shipped |
| Seed data | ✅ Shipped |
| Read-only SQL execution tool | ✅ Shipped |
| SQL safety validation | ✅ Shipped |
| Deterministic analytics routing | ✅ Shipped |
| LangGraph analytics workflow | ✅ Shipped |
| FastAPI application | ✅ Shipped |
| `/health` endpoint | ✅ Shipped |
| `/agent` endpoint | ✅ Shipped |
| API response schemas | ✅ Shipped |
| Automated API/tool tests | ✅ Shipped |
| GitHub version control | ✅ Shipped |

**Current baseline: 65 automated tests passing.**

The Phase 1 baseline is the foundation that all subsequent phases must preserve. Existing tests must continue passing as new capabilities are added.

---

# Roadmap

## Phase 2 — Production API and multi-organisation architecture

**Status: 🚧 Next major phase**

Goal: turn the current single-dataset analytics API into a properly scoped enterprise platform.

### Work items

- [ ] Finalise organisation model and relationships
- [ ] Add organisation-aware request context
- [ ] Enforce organisation scoping at the database/query layer
- [ ] Prevent cross-organisation data leakage
- [ ] Add organisation management API
- [ ] Add API versioning strategy
- [ ] Formalise request/response contracts
- [ ] Add authentication foundation
- [ ] Add role/permission model
- [ ] Add tenant-isolation tests
- [ ] Add database session/dependency patterns suitable for production
- [ ] Remove remaining hard-coded single-organisation assumptions

### Exit criteria

- Every analytics request can be scoped to an organisation.
- Organisation A cannot access Organisation B's records.
- Existing Phase 1 tests remain green.
- New tenant-isolation tests are green.
- API contracts are documented and stable.

---

## Phase 3 — LLM-powered analytics agent

**Status: ⬜ Planned**

Replace the initial deterministic/rule-based question handling with controlled LLM reasoning while retaining the existing safety boundaries.

### Work items

- [ ] LLM provider abstraction
- [ ] Schema-aware text-to-SQL generation
- [ ] Intent classification/router
- [ ] SQL generation prompt architecture
- [ ] SQL validation before execution
- [ ] SQL query repair loop
- [ ] Result interpretation
- [ ] Natural-language answer generation
- [ ] Structured citations/source metadata
- [ ] Model fallback strategy
- [ ] LLM evaluation dataset
- [ ] Regression tests for generated SQL
- [ ] Cost and latency tracking

### Important principle

The LLM must **not** receive unrestricted database execution privileges. Generated SQL must pass the safety layer and database permissions before execution.

---

## Phase 4 — External RAG

**Status: ⬜ Planned**

Add retrieval over unstructured organisational knowledge.

### Work items

- [ ] Document ingestion pipeline
- [ ] PDF/document parsing
- [ ] Chunking strategy
- [ ] Embedding generation
- [ ] Vector database/store
- [ ] Metadata filtering
- [ ] Organisation-specific knowledge collections
- [ ] Semantic retrieval
- [ ] Hybrid retrieval
- [ ] Reranking
- [ ] Retrieval citations
- [ ] Document provenance
- [ ] RAG evaluation set

### Target behaviour

The agent should be able to determine whether a question requires:

1. structured SQL data,
2. unstructured organisational knowledge,
3. both SQL and RAG, or
4. another external source.

---

## Phase 5 — Multi-source intelligence

**Status: ⬜ Planned**

Connect multiple information sources behind a controlled routing layer.

### Sources

- [ ] PostgreSQL
- [ ] Organisational documents
- [ ] External knowledge bases
- [ ] Live web search
- [ ] External APIs
- [ ] Structured files
- [ ] Customer-provided data sources

### Work items

- [ ] Source/tool registry
- [ ] Source routing
- [ ] Source prioritisation
- [ ] Cross-source reasoning
- [ ] Provenance tracking
- [ ] Conflict handling between sources
- [ ] Unified answer synthesis

---

## Phase 6 — MCP and enterprise tool ecosystem

**Status: ⬜ Planned**

Introduce a standardised tool interface for external systems.

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

The agent should be able to use tools deliberately rather than simply generating text.

---

## Phase 7 — Advanced agent architecture

**Status: ⬜ Planned**

Evolve the current analytics workflow into a controlled agent system.

### Planned components

- [ ] Supervisor/router
- [ ] Analytics agent
- [ ] SQL agent/tool
- [ ] RAG agent
- [ ] Web research agent
- [ ] External-tool agent
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

Build evaluation into the platform rather than treating it as a final step.

### Work items

- [ ] Golden question dataset
- [ ] SQL correctness evaluation
- [ ] Intent classification evaluation
- [ ] Retrieval precision/recall evaluation
- [ ] Answer quality evaluation
- [ ] Citation/provenance evaluation
- [ ] Hallucination tests
- [ ] Agent trajectory evaluation
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
- [ ] Security testing

Security controls must exist at multiple layers; prompt instructions alone are not considered a security boundary.

---

## Phase 10 — Observability and production infrastructure

**Status: ⬜ Planned**

### Work items

- [ ] Structured application logging
- [ ] Agent execution tracing
- [ ] Metrics
- [ ] Request latency monitoring
- [ ] SQL execution monitoring
- [ ] Retrieval monitoring
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
                    |   Agent Router    |
                    +---------+---------+
                              |
        +---------------------+---------------------+
        |                     |                     |
      SQL/RDB              External RAG         Web/APIs
        |                     |                     |
   Customer DB          Customer KBs          External data
        |                     |                     |
        +---------------------+---------------------+
                              |
                       Synthesis/Answer
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

The current production path is intentionally simple and controlled:

```text
User
  |
  v
FastAPI /agent
  |
  v
Analytics Agent (LangGraph)
  |
  +--> Intent / SQL generation
  |
  +--> SQL safety validation
  |
  +--> PostgreSQL
  |
  v
Structured result
  |
  v
Agent response
```

This will evolve incrementally. We should not introduce additional agents, RAG, MCP, or external services merely for architectural appearance. Each component must solve a demonstrated requirement and have tests/evaluation around it.

---

# Development rules

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

---

# Current verification baseline

Last known local verification before continuing development:

```text
65 passed in 0.72s
```

The `/agent` endpoint has also been manually verified with:

```text
POST /agent
{
  "question": "How many franchisees are there?"
}
```

and returned a successful structured response containing the intent, SQL query, result and PostgreSQL source.

---

# Next immediate milestone

## Phase 2 — Multi-organisation foundation

The next implementation sequence is:

1. Review the current GitHub codebase.
2. Confirm the current schema and existing organisation model.
3. Define organisation relationships and ownership boundaries.
4. Add organisation-aware API request handling.
5. Scope analytics queries by organisation.
6. Add organisation isolation tests.
7. Add organisation management/read endpoints where required.
8. Run the complete test suite.
9. Update this README's tracking table.
10. Commit the completed phase increment.
11. Push to GitHub.
12. Only then begin the next architectural extension.

This sequence is intentionally strict so that the project remains reproducible and we always have a known-good checkpoint.

---

# Repository

GitHub: `james00junior/ECD-Intelligence-Platform`

The repository history is the authoritative record of implementation progress. The README is the authoritative roadmap and feature-tracking document.
