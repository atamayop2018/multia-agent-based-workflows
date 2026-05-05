import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################

# ---------------------------------------------------------------------------
# Multi-Agent System (pydantic-ai)
# ---------------------------------------------------------------------------
# Architecture (4 agents, well below the 5-agent cap):
#
#   ┌──────────────────────────────────────────────────────────────────────┐
#   │                       OrchestratorAgent                              │
#   │   - Parses customer request                                          │
#   │   - Delegates to specialist agents in sequence                       │
#   │   - Returns a final natural-language reply                           │
#   └────────────┬───────────────────────┬───────────────────┬─────────────┘
#                │                       │                   │
#                ▼                       ▼                   ▼
#       ┌────────────────┐      ┌────────────────┐   ┌────────────────┐
#       │ InventoryAgent │      │ QuotingAgent   │   │ OrderingAgent  │
#       │ stock checks,  │      │ history search │   │ finalize sale, │
#       │ reorder logic  │      │ & quote calc   │   │ write txns     │
#       └────────────────┘      └────────────────┘   └────────────────┘
#
# Communication is text-based (JSON strings between agents). Each specialist
# is exposed to the orchestrator through a thin wrapper tool function.
# ---------------------------------------------------------------------------

import json
import re
from typing import Any, Optional

dotenv.load_dotenv()

_API_KEY = (
    os.environ.get("UDACITY_OPENAI_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
    or ""
)
_BASE_URL = os.environ.get(
    "OPENAI_BASE_URL", "https://openai.vocareum.com/v1"
)
_MODEL_NAME = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Lazy import so the module remains importable even if pydantic-ai is missing.
try:
    import httpx
    from openai import AsyncOpenAI
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider
    from pydantic_ai.settings import ModelSettings

    # Hardened HTTP client: connect/read timeouts so a hung call cannot stall the
    # whole batch (the un-timed default would block forever, as we observed).
    _http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=15.0, read=60.0, write=30.0, pool=15.0)
    )
    _openai_client = AsyncOpenAI(
        api_key=_API_KEY, base_url=_BASE_URL, http_client=_http_client, max_retries=2
    )
    _provider = OpenAIProvider(openai_client=_openai_client)
    _model = OpenAIChatModel(_MODEL_NAME, provider=_provider)
    _MODEL_SETTINGS = ModelSettings(timeout=60.0, max_tokens=1024)
    _PYDANTIC_AI_AVAILABLE = True
except Exception as _e:  # pragma: no cover
    print(f"WARN: pydantic-ai unavailable ({_e}); will use fallback runner.")
    Agent = None  # type: ignore
    _model = None
    _MODEL_SETTINGS = None
    _PYDANTIC_AI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Helper tools that combine raw DB primitives with business rules
# ---------------------------------------------------------------------------

# Cache the canonical item catalogue for fuzzy matching.
_ITEM_NAME_LOOKUP = {p["item_name"].lower(): p["item_name"] for p in paper_supplies}
_UNIT_PRICES = {p["item_name"]: p["unit_price"] for p in paper_supplies}


def _resolve_item_name(name: str) -> Optional[str]:
    """Map a free-form item description to a canonical catalogue name."""
    if not name:
        return None
    key = name.strip().lower()
    if key in _ITEM_NAME_LOOKUP:
        return _ITEM_NAME_LOOKUP[key]
    # try partial / token match
    tokens = [t for t in re.split(r"\W+", key) if t]
    best = None
    best_score = 0
    for canonical_lower, canonical in _ITEM_NAME_LOOKUP.items():
        score = sum(1 for t in tokens if t in canonical_lower)
        if score > best_score:
            best_score = score
            best = canonical
    return best if best_score > 0 else None


def tool_check_inventory(item_name: str, as_of_date: str) -> str:
    """Return JSON: {item_name, canonical_name, current_stock, min_stock_level, unit_price}."""
    canonical = _resolve_item_name(item_name) or item_name
    df = get_stock_level(canonical, as_of_date)
    stock = int(df["current_stock"].iloc[0]) if not df.empty else 0
    inv = pd.read_sql(
        "SELECT min_stock_level, unit_price FROM inventory WHERE item_name = :n",
        db_engine,
        params={"n": canonical},
    )
    min_level = int(inv["min_stock_level"].iloc[0]) if not inv.empty else 0
    unit_price = (
        float(inv["unit_price"].iloc[0]) if not inv.empty else _UNIT_PRICES.get(canonical, 0.0)
    )
    return json.dumps(
        {
            "requested_item": item_name,
            "canonical_name": canonical,
            "current_stock": stock,
            "min_stock_level": min_level,
            "unit_price": unit_price,
        }
    )


def tool_list_inventory(as_of_date: str) -> str:
    """Return JSON of the full inventory snapshot as of the given date."""
    inv = get_all_inventory(as_of_date)
    return json.dumps(inv)


def tool_restock_item(item_name: str, quantity: int, as_of_date: str) -> str:
    """Place a stock_orders transaction at unit cost; respects available cash."""
    canonical = _resolve_item_name(item_name) or item_name
    unit_price = _UNIT_PRICES.get(canonical)
    if unit_price is None:
        return json.dumps({"ok": False, "reason": f"Unknown item '{item_name}'"})
    cost = round(unit_price * quantity, 2)
    cash = get_cash_balance(as_of_date)
    if cost > cash:
        return json.dumps(
            {"ok": False, "reason": f"Insufficient cash ${cash:.2f} for cost ${cost:.2f}"}
        )
    delivery_date = get_supplier_delivery_date(as_of_date, quantity)
    create_transaction(canonical, "stock_orders", int(quantity), cost, delivery_date)
    return json.dumps(
        {
            "ok": True,
            "item_name": canonical,
            "units": int(quantity),
            "cost": cost,
            "delivery_date": delivery_date,
        }
    )


def tool_search_history(search_terms: List[str], limit: int = 5) -> str:
    """Search historical quotes."""
    rows = search_quote_history(search_terms, limit=limit)
    # Make JSON-safe (datetime, etc.)
    return json.dumps(rows, default=str)


def tool_compute_quote(line_items: List[Dict], order_size: str = "small") -> str:
    """
    Compute a quote total with tiered bulk discounts.

    line_items: [{"item_name": str, "quantity": int}]
    """
    breakdown = []
    subtotal = 0.0
    total_units = 0
    for li in line_items:
        canonical = _resolve_item_name(li.get("item_name", "")) or li.get("item_name", "")
        qty = int(li.get("quantity", 0))
        unit_price = _UNIT_PRICES.get(canonical, 0.0)
        line_total = round(unit_price * qty, 2)
        subtotal += line_total
        total_units += qty
        breakdown.append(
            {
                "item_name": canonical,
                "quantity": qty,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )
    # Bulk discount tiers
    if total_units >= 1000 or order_size.lower() == "large":
        discount_pct = 0.10
    elif total_units >= 250 or order_size.lower() == "medium":
        discount_pct = 0.05
    else:
        discount_pct = 0.0
    discount = round(subtotal * discount_pct, 2)
    total = round(subtotal - discount, 2)
    return json.dumps(
        {
            "breakdown": breakdown,
            "subtotal": round(subtotal, 2),
            "discount_pct": discount_pct,
            "discount_amount": discount,
            "total": total,
            "total_units": total_units,
        }
    )


def tool_finalize_sale(line_items: List[Dict], total_price: float, as_of_date: str) -> str:
    """
    Record a sales transaction per line item if all stock is available.
    Returns JSON describing committed sale or the failure reason.
    """
    # Validate stock
    shortages = []
    resolved = []
    for li in line_items:
        canonical = _resolve_item_name(li.get("item_name", "")) or li.get("item_name", "")
        qty = int(li.get("quantity", 0))
        df = get_stock_level(canonical, as_of_date)
        stock = int(df["current_stock"].iloc[0]) if not df.empty else 0
        if stock < qty:
            shortages.append({"item_name": canonical, "available": stock, "requested": qty})
        resolved.append({"item_name": canonical, "quantity": qty})
    if shortages:
        return json.dumps({"ok": False, "reason": "insufficient_stock", "shortages": shortages})

    # Distribute total price proportionally so per-item revenue makes sense.
    # Use catalogue subtotal for proportions; fall back to equal split if zero.
    weights = []
    for r in resolved:
        weights.append(_UNIT_PRICES.get(r["item_name"], 0.0) * r["quantity"])
    weight_sum = sum(weights)
    if weight_sum <= 0:
        weights = [1.0] * len(resolved)
        weight_sum = float(len(resolved))

    delivery_date = get_supplier_delivery_date(as_of_date, sum(r["quantity"] for r in resolved))
    txn_ids = []
    for r, w in zip(resolved, weights):
        share = round(total_price * (w / weight_sum), 2)
        tid = create_transaction(
            r["item_name"], "sales", r["quantity"], share, as_of_date
        )
        txn_ids.append(tid)
    return json.dumps(
        {
            "ok": True,
            "transaction_ids": txn_ids,
            "total_revenue": round(total_price, 2),
            "delivery_date": delivery_date,
        }
    )


def tool_get_cash(as_of_date: str) -> str:
    return json.dumps({"cash_balance": round(get_cash_balance(as_of_date), 2)})


def tool_financial_report(as_of_date: str) -> str:
    """
    Return a JSON snapshot of the company's financial position as of the given
    date. Wraps :func:`generate_financial_report` so the orchestrator can
    consult cash balance, inventory valuation, total assets, per-item stock
    summary and top-selling products before committing large quotes.
    """
    report = generate_financial_report(as_of_date)
    return json.dumps(report, default=str)


# ---------------------------------------------------------------------------
# Customer-reply sanitizer
# ---------------------------------------------------------------------------
# The LLM occasionally leaks internal data into the customer-facing reply
# (transaction IDs, raw cash-balance failure messages, "[Your Name]" template
# placeholders copied from historical emails). We strip those before returning
# the final response so the customer sees only business-appropriate content.

_INTERNAL_LINE_PATTERNS = [
    re.compile(r"transaction[_ ]id", re.IGNORECASE),
    re.compile(r"\btxn[_ ]?ids?\b", re.IGNORECASE),
    re.compile(r"inadequate cash balance", re.IGNORECASE),
    re.compile(r"insufficient cash", re.IGNORECASE),
    re.compile(r"cash balance (?:is|of)\s*\$", re.IGNORECASE),
    re.compile(r"cannot initiate a restock", re.IGNORECASE),
]

_PLACEHOLDER_REPLACEMENTS = [
    (re.compile(r"\[Your Name\]"), "The Beaver's Choice Team"),
    (re.compile(r"\[Your Position\]"), "Customer Care"),
    (re.compile(r"\[Your Business Name\]"), "Beaver's Choice Paper Company"),
    (re.compile(r"\[Hotel Name\]"), "Beaver's Choice Paper Company"),
]


def _sanitize_customer_reply(text: str) -> str:
    """Strip internal artefacts and resolve template placeholders."""
    if not text:
        return text
    # Drop lines that leak internal-only data.
    cleaned_lines = []
    for line in text.splitlines():
        if any(p.search(line) for p in _INTERNAL_LINE_PATTERNS):
            continue
        cleaned_lines.append(line)
    out = "\n".join(cleaned_lines)
    # Resolve placeholders.
    for pattern, replacement in _PLACEHOLDER_REPLACEMENTS:
        out = pattern.sub(replacement, out)
    # Collapse 3+ blank lines to a single blank line.
    out = re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"
    return out


# ---------------------------------------------------------------------------
# Specialist agents
# ---------------------------------------------------------------------------

if _PYDANTIC_AI_AVAILABLE:

    inventory_agent = Agent(
        _model,
        name="InventoryAgent",
        system_prompt=(
            "You are the Inventory Agent for Beaver's Choice Paper Company.\n"
            "Given a list of items with desired quantities and a request date, "
            "you check stock levels, decide whether to restock items that fall "
            "below their minimum stock threshold, and return a concise JSON "
            "report. Always use the provided tools. Respond with a JSON object "
            "containing keys: availability (list of {item_name, requested, "
            "available, sufficient}), restocked (list of restock actions), and "
            "notes (string)."
        ),
        tools=[tool_check_inventory, tool_list_inventory, tool_restock_item, tool_get_cash],
    )

    quoting_agent = Agent(
        _model,
        name="QuotingAgent",
        system_prompt=(
            "You are the Quoting Agent. Use historical quote data and the "
            "compute_quote tool to produce a fair, customer-friendly quote. "
            "Apply bulk discounts (5% for medium >=250 units, 10% for large "
            ">=1000 units or order_size=large). Always call tool_compute_quote "
            "to obtain the authoritative total. Respond with a JSON object: "
            "{line_items, subtotal, discount_pct, total, explanation}."
        ),
        tools=[tool_search_history, tool_compute_quote],
    )

    ordering_agent = Agent(
        _model,
        name="OrderingAgent",
        system_prompt=(
            "You are the Ordering Agent. Given approved line_items, the agreed "
            "total price, and the request date, finalize the sale by calling "
            "tool_finalize_sale. If stock is insufficient, return the shortage "
            "info. Respond with the tool's JSON result verbatim."
        ),
        tools=[tool_finalize_sale, tool_check_inventory],
    )

    # ------- Orchestrator wraps the specialists as tools -------------------

    def _run_specialist(agent: "Agent", prompt: str) -> str:
        try:
            res = agent.run_sync(prompt, model_settings=_MODEL_SETTINGS)
            return str(res.output)
        except Exception as ex:
            return json.dumps({"ok": False, "error": str(ex)})

    def delegate_to_inventory(instruction: str) -> str:
        """Ask the InventoryAgent to check/restock items. `instruction` is plain text."""
        return _run_specialist(inventory_agent, instruction)

    def delegate_to_quoting(instruction: str) -> str:
        """Ask the QuotingAgent to compute a quote. `instruction` is plain text."""
        return _run_specialist(quoting_agent, instruction)

    def delegate_to_ordering(instruction: str) -> str:
        """Ask the OrderingAgent to finalize a sale. `instruction` is plain text."""
        return _run_specialist(ordering_agent, instruction)

    orchestrator_agent = Agent(
        _model,
        name="OrchestratorAgent",
        system_prompt=(
            "You are the Orchestrator for Beaver's Choice Paper Company's "
            "multi-agent quoting system. For every customer request you must:\n"
            "1. Parse the request into line items (item_name, quantity) and "
            "   note the request date.\n"
            "2. Call delegate_to_inventory to verify stock and trigger any "
            "   needed restocks.\n"
            "3. Call delegate_to_quoting to compute the customer quote (with "
            "   appropriate bulk discount).\n"
            "4. Call delegate_to_ordering to finalize the sale at the quoted "
            "   total. If stock cannot be satisfied even after restock, "
            "   politely decline that line.\n"
            "5. Reply to the customer with a single concise, professional "
            "   message that includes: the itemised quote, total, any "
            "   discounts applied, expected delivery date, and confirmation "
            "   that the order has been recorded (or an apology if not).\n"
            "Always pass the request date through to every specialist.\n"
            "IMPORTANT customer-facing rules: never include internal data in "
            "the final reply (no transaction IDs, no raw cash-balance "
            "numbers, no internal failure reasons such as 'insufficient "
            "cash'). If a sale cannot be fulfilled, apologise generically "
            "and offer to follow up. Sign every reply as "
            "'The Beaver's Choice Team' — never use placeholders such as "
            "'[Your Name]'. You may call tool_financial_report or "
            "tool_get_cash internally, but their results must NOT appear in "
            "the customer message."
        ),
        tools=[
            delegate_to_inventory,
            delegate_to_quoting,
            delegate_to_ordering,
            tool_get_cash,
            tool_financial_report,
        ],
    )


def _run_orchestrator_once(
    request_with_date: str, hard_timeout: float
) -> Dict[str, Any]:
    """Execute one orchestrator call in a worker thread with a hard timeout."""
    import threading

    box: Dict[str, Any] = {}

    def _worker() -> None:
        try:
            result = orchestrator_agent.run_sync(
                request_with_date, model_settings=_MODEL_SETTINGS
            )
            box["output"] = str(result.output)
        except Exception as ex:  # pragma: no cover - network dependent
            box["error"] = repr(ex)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(hard_timeout)
    if t.is_alive():
        box["timeout"] = True
    return box


def call_multi_agent_system(
    request_with_date: str,
    hard_timeout: float = 180.0,
    max_attempts: int = 3,
) -> str:
    """Public entry-point used by run_test_scenarios.

    Each attempt is bounded by a hard wall-clock timeout. Transient connection
    errors and timeouts trigger a brief exponential back-off retry up to
    ``max_attempts`` times so a flaky network does not pollute the results.
    """
    if not _PYDANTIC_AI_AVAILABLE:
        return "[multi-agent system disabled: pydantic-ai not installed]"

    last_error = None
    for attempt in range(1, max_attempts + 1):
        outcome = _run_orchestrator_once(request_with_date, hard_timeout)
        if "output" in outcome:
            return _sanitize_customer_reply(outcome["output"])
        if outcome.get("timeout"):
            last_error = f"timeout after {hard_timeout:.0f}s"
        else:
            last_error = outcome.get("error", "unknown error")
        if attempt < max_attempts:
            backoff = 2 ** attempt  # 2s, 4s, ...
            print(
                f"  [retry {attempt}/{max_attempts-1}] {last_error}; "
                f"sleeping {backoff}s",
                flush=True,
            )
            time.sleep(backoff)
    return f"[orchestrator failed after {max_attempts} attempts: {last_error}]"


# ---------------------------------------------------------------------------
# Test scenario driver
# ---------------------------------------------------------------------------

def run_test_scenarios():
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    print(f"\nStarting Cash:      ${current_cash:.2f}")
    print(f"Starting Inventory: ${current_inventory:.2f}\n")

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        request_with_date = (
            f"{row['request']}\n\n"
            f"Customer profile: job={row['job']}, event={row['event']}, "
            f"need_size={row.get('need_size', 'unknown')}.\n"
            f"Date of request: {request_date}.\n"
            f"Use {request_date} for every tool call requiring a date."
        )

        try:
            response = call_multi_agent_system(request_with_date)
        except Exception as exc:
            response = f"[error: {exc}]"

        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        # Incrementally persist progress so a crash mid-run still leaves
        # partial results on disk for inspection.
        pd.DataFrame(results).to_csv("test_results.csv", index=False)
        time.sleep(0.2)

    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash:      ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")
    print(f"Total Assets:    ${final_report['total_assets']:.2f}")

    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
