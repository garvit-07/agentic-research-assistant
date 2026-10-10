# Interview guide for this project

## Resume bullets (pick 3 to 4)

- Built a multi-step **LangGraph** research agent that plans tasks, calls tools (web search, RAG over uploaded documents), and **self-reviews** drafts with a scored critique loop before answering.
- Exposed the agent through **async FastAPI** with **Server-Sent Events** streaming of plans, tool calls and tokens, plus SQLite-checkpointed **persistent memory** per conversation thread.
- Implemented bounded control flow (step, tool and revision budgets), structured outputs with Pydantic, optional API-key auth, health probes and automated tests in **GitHub Actions** CI.
- **Containerised** with a multi-stage, non-root Docker image, healthcheck and volume-backed persistence.

## 60-second pitch

"I built a research assistant as a graph rather than a single prompt. A planner breaks the question into steps, a researcher runs each step with web search and a document retriever, a writer drafts the answer, and a reviewer scores it. If the score is low, the draft goes back to the writer with specific feedback, up to a limit. The agent is served by async FastAPI with streaming, so the user sees the plan, tool calls and tokens live. Conversation state is checkpointed to SQLite, so memory survives restarts, and everything runs in Docker."

## Likely questions and strong answers

**Why LangGraph instead of a plain LangChain agent?**
I needed explicit control flow: conditional edges, a revision cycle and bounded loops. A graph makes each step observable, testable and checkpointable, which a single opaque agent loop does not.

**How does the self-review work, and can it loop forever?**
The reviewer returns structured output (approved, score, issues, feedback). A conditional edge sends rejected drafts back to the writer. `MAX_REVISIONS` caps the cycle and a graph `recursion_limit` is a second safety net.

**How does memory work?**
LangGraph's `AsyncSqliteSaver` checkpoints state after every node, keyed by `thread_id`. Only chat messages carry across turns; per-turn working state is reset so earlier research does not contaminate a new question.

**How do you stream?**
`graph.astream_events(version="v2")` emits node starts, tool calls and chat-model token chunks. I filter writer tokens and map events to SSE. A new writer `node_start` tells the client a revision began.

**How do you reduce hallucination?**
Retrieval and search grounding, a writer prompt that forbids unsupported claims and requires citations, and a reviewer that checks claims against the findings.

**What would you change for production at scale?**
Swap SQLite for the Postgres checkpointer, use a hosted vector DB, add rate limiting and real auth, run several replicas behind a load balancer, add tracing (LangSmith or OpenTelemetry) and an offline evaluation set.

**How would you evaluate it?**
Build a labelled question set; measure answer faithfulness to retrieved context, citation correctness, tool-call success rate, latency and cost per answer; track reviewer scores over time.

**What are the weaknesses?**
The reviewer is an LLM judging an LLM, so it can miss errors. Research steps run sequentially (they could run in parallel). DuckDuckGo results vary in quality. Mention these before the interviewer does.

## Demo checklist

1. `docker compose up --build`, open the UI.
2. Upload a PDF, ask a question about it and show the `search_documents` tool call.
3. Ask a current-events question and show `web_search`.
4. Ask a follow-up ("summarise that") to demonstrate memory, then restart the container and repeat it with the same thread.
5. Open `/docs` to show the API, and the GitHub Actions run to show CI.
