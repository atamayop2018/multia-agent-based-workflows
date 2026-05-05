# Workflow Diagram

```mermaid
flowchart TD
    C([Customer Request<br/>+ request_date]) --> O[OrchestratorAgent]

    O -->|"delegate_to_inventory<br/>(items, qty, date)"| I[InventoryAgent]
    I -->|tool_check_inventory| DB[(SQLite<br/>transactions / inventory)]
    I -->|tool_restock_item| DB
    I -->|JSON: availability + restocks| O

    O -->|"delegate_to_quoting<br/>(items, qty, history)"| Q[QuotingAgent]
    Q -->|tool_search_history| DB
    Q -->|tool_compute_quote| Q
    Q -->|"JSON: subtotal, discount, total, explanation"| O

    O -->|"delegate_to_ordering<br/>(items, total, date)"| R[OrderingAgent]
    R -->|tool_finalize_sale| DB
    R -->|JSON: txn_ids, revenue, delivery| O

    O --> A([Final natural-language<br/>reply to customer<br/>+ persisted sale])

    classDef agent fill:#e1f0ff,stroke:#3a7bbf,color:#000;
    classDef store fill:#fff5cc,stroke:#bf9b3a,color:#000;
    class O,I,Q,R agent;
    class DB store;
```

## Sequence per request

```mermaid
sequenceDiagram
    autonumber
    participant U as Customer
    participant O as OrchestratorAgent
    participant I as InventoryAgent
    participant Q as QuotingAgent
    participant R as OrderingAgent
    participant DB as SQLite DB

    U->>O: request + date
    O->>I: items + qty + date
    I->>DB: stock & min_stock lookups
    I-->>O: availability + restocks
    O->>Q: items + qty + size
    Q->>DB: search_quote_history
    Q-->>O: subtotal / discount / total
    O->>R: items + total + date
    R->>DB: validate stock + write sales txns
    R-->>O: txn ids + delivery date
    O-->>U: itemised reply with confirmation
```

## Discount tiers

| Order size                                   | Discount |
|----------------------------------------------|----------|
| ≥1000 units, or `order_size == large`        | **10%**  |
| ≥250 units, or `order_size == medium`        | **5%**   |
| otherwise                                    | 0%       |
