# Beaver's Choice / Munder Difflin — Multi-Agent System Design Notes

## Overview

This project delivers a **4-agent system** (within the 5-agent cap) built on
[`pydantic-ai`](https://ai.pydantic.dev/) that automates Beaver's Choice Paper
Company's quoting and order workflow. All inputs and outputs are text-based and
the system is driven by the test harness in
[`run_test_scenarios()`](project_starter.py:1).

## Agent Roster

| # | Agent              | Responsibility                                                                 | Key tools                                                                 |
|---|--------------------|--------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| 1 | `OrchestratorAgent`| Parses each customer request, sequences the workflow, returns the final reply  | `delegate_to_inventory`, `delegate_to_quoting`, `delegate_to_ordering`, `tool_get_cash` |
| 2 | `InventoryAgent`   | Verifies stock per item; restocks below-minimum items via supplier transactions| `tool_check_inventory`, `tool_list_inventory`, `tool_restock_item`, `tool_get_cash` |
| 3 | `QuotingAgent`     | Looks up historical quotes and computes a tiered-discount quote                | `tool_search_history`, `tool_compute_quote`                              |
| 4 | `OrderingAgent`    | Finalizes the sale by writing per-item `sales` transactions if stock suffices  | `tool_finalize_sale`, `tool_check_inventory`                             |

The orchestrator exposes the three specialists as text-in / text-out tools
(`delegate_to_*`). Each delegate call internally invokes `Agent.run_sync` on the
corresponding specialist so that communication between agents is purely
text/JSON, satisfying the project's text-only I/O constraint.

## Workflow

```
Customer request ──▶ OrchestratorAgent
                         │
                         ├─▶ InventoryAgent  ──▶ check_inventory / restock_item
                         │                       (DB: transactions, inventory)
                         │
                         ├─▶ QuotingAgent    ──▶ search_history / compute_quote
                         │                       (DB: quotes, quote_requests)
                         │
                         └─▶ OrderingAgent   ──▶ finalize_sale (DB: transactions)
                         │
                         ▼
                Final natural-language reply to customer
```

A flowchart-friendly version of the diagram is in
[`workflow_diagram.md`](workflow_diagram.md).

## Business Rules Implemented

- **Item resolution.** `_resolve_item_name` performs a case-insensitive lookup
  with token-level fallback so user-supplied names (e.g. `"a4 paper"`) map to
  the canonical catalogue (`"A4 paper"`), preventing transaction failures.
- **Stock check & restock.** When the inventory agent sees an item with stock
  below `min_stock_level`, it places a `stock_orders` transaction sized to the
  shortfall plus a buffer. Restocks are bounded by available cash.
- **Bulk discount tiers** (in `tool_compute_quote`):
  - `>=1000` units **or** `order_size == "large"` → **10%** discount
  - `>=250`  units **or** `order_size == "medium"` → **5%** discount
  - otherwise → no discount
- **Sale finalization.** `tool_finalize_sale` validates current stock per line
  before recording any `sales` transaction; if any line is short the entire
  sale is rejected with a structured shortage report.
- **Delivery dates.** `get_supplier_delivery_date` is reused from the starter
  utilities (same-day / +1d / +4d / +7d depending on quantity).

## Robustness Features

- **HTTP timeouts.** A custom `httpx.AsyncClient` with `connect=15s` /
  `read=60s` is wired into `OpenAIProvider` so a hung upstream cannot stall the
  batch (we observed an indefinite kqueue wait without this).
- **Per-request hard timeout.** `call_multi_agent_system` runs the orchestrator
  in a worker thread bounded by a 180-second wall-clock budget; on timeout the
  orchestrator returns a sentinel string instead of blocking the suite.
- **Retries.** `AsyncOpenAI(max_retries=2)` plus `ModelSettings(timeout=60)`
  provide bounded retry behavior on transient network errors.
- **Incremental persistence.** `test_results.csv` is rewritten after every
  request, so a crash mid-run still leaves partial results on disk.

## File Map

| File                   | Purpose                                                  |
|------------------------|----------------------------------------------------------|
| `project_starter.py`   | All agents, tools, DB utilities, test driver             |
| `quote_requests.csv`   | Historical customer requests (loaded into `quote_requests` table) |
| `quotes.csv`           | Historical quotes (loaded into `quotes` table)           |
| `quote_requests_sample.csv` | Test scenarios driven by `run_test_scenarios()`     |
| `munder_difflin.db`    | SQLite DB (re-created on each run)                       |
| `test_results.csv`     | Per-request audit log produced by the run                |
| `run.log`              | Captured stdout/stderr from the most recent batch        |
| `design_notes.md`      | This document                                            |
| `workflow_diagram.md`  | Mermaid workflow diagram                                 |

## How to Run

```bash
cd project
python -u project_starter.py
```

`UDACITY_OPENAI_API_KEY` must be set in `.env` (or the environment). The
endpoint defaults to `https://openai.vocareum.com/v1` and the model to
`gpt-4o-mini`; both are overridable via `OPENAI_BASE_URL` / `OPENAI_MODEL`.
