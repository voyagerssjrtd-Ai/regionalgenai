from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
import pandas as pd
from langchain_openai import ChatOpenAI
import httpx
import requests

def security():
    for method in ("get","post","put","delete","head","options","patch"):
        original = getattr(requests,method)
    def insecure_request(*args, _original = original, **kwargs):
        kwargs["verify"] = False
        return _original(*args,**kwargs)
    setattr(requests,method,insecure_request)

# Create an HTTP client that skips SSL verification (only for hackathon/test environments)
def getllm(query):  
    client = httpx.Client(verify=False)
    llm = ChatOpenAI(
        base_url="https://genailab.tcs.in",
        model="azure/genailab-maas-gpt-4o",
        api_key="sk-K5cCB7yk7rc3ex2NV3-TWw",
        http_client=client)
    return llm.invoke(query)

class State(TypedDict):
   application: str
   input_keyword: str
   sql_query: str
   response: str

workflow = StateGraph(State)

# --- Helpers ---
def normalize_dates(purchase_order_df: pd.DataFrame, inventory_stock_df: pd.DataFrame):
    # Convert to datetime (your input is DD-MM-YYYY)
    for col in ["OrderDate", "ExpectedDeliveryDate", "ActualReciptDate"]:
        purchase_order_df[col] = pd.to_datetime(purchase_order_df[col], dayfirst=True, errors="coerce")
    inventory_stock_df["LastUpdated"] = pd.to_datetime(inventory_stock_df["LastUpdated"], dayfirst=True, errors="coerce")
    return purchase_order_df, inventory_stock_df

def build_tabular_output(inventory_stock_df: pd.DataFrame, purchase_order_df: pd.DataFrame):
    # Reference date: latest LastUpdated present in inventory
    ref_date = inventory_stock_df["LastUpdated"].max().date()

    # Products that reached or fell below ReorderPoint on the reference date
    reached = inventory_stock_df[
        (inventory_stock_df["CurrentStock"] <= inventory_stock_df["ReorderPoint"]) &
        (inventory_stock_df["LastUpdated"].dt.date == ref_date)
    ][["ProductId", "CurrentStock", "ReorderPoint", "LastUpdated"]].copy()

    # Orders placed on the same reference date
    orders_today = purchase_order_df[purchase_order_df["OrderDate"].dt.date == ref_date][["ProductId", "Status"]].copy()

    # Left join reached products with orders
    result = reached.merge(orders_today, on="ProductId", how="left")

    # Comment column
    def comment_row(row):
        if pd.notna(row["Status"]) and row["Status"] == "ORDER_PLACED":
            return "Order placed successfully"
        # Give a reason when no order placed
        return f"No order placed - stock {row['CurrentStock']} <= reorder {row['ReorderPoint']} on {row['LastUpdated'].date()}"

    result["Comment"] = result.apply(comment_row, axis=1)
    # Keep only required columns
    return result[["ProductId", "Status", "Comment"]]

# --- Summary function: generate SQL (for transparency) and compute correct result in pandas ---
def summary(state: State) -> State:
    # Data
    purchase_order = {
        "PONumber": ["123", "456", "789"],
        "ProductId": ["A123", "B123", "C123"],
        "SupplierId": [111, 222, 333],
        "OrderDate": ["18-11-2025", "18-11-2025", "18-11-2025"],
        "ExpectedDeliveryDate": ["25-11-2025", "30-11-2025", "22-11-2025"],
        "ActualReciptDate": ["18-11-2025", "18-11-2025", "18-11-2025"],
        "Status": ["ORDER_PLACED", "ORDER_PLACED", "ORDER_PLACED"],
        "TotalCost": [2000, 5000, 2000]
    }
    inventory_stock = {
        "InventoryId": ["1", "2", "3"],
        "ProductId": ["A123", "B123", "C123"],
        "WareHouseId": ["123", "123", "123"],
        "CurrentStock": [15, 55, 8],
        "ReorderPoint": [20, 50, 10],
        "SafetyStock": [5, 10, 2],
        "LastUpdated": ["18-11-2025", "17-11-2025", "18-11-2025"]
    }
    purchase_order_df = pd.DataFrame(purchase_order)
    inventory_stock_df = pd.DataFrame(inventory_stock)

    # Normalize dates
    purchase_order_df, inventory_stock_df = normalize_dates(purchase_order_df, inventory_stock_df)

    # Prompt (generate SQL for visibility, but execution uses pandas)
    prompt = ChatPromptTemplate.from_template(
        "You are a highly skilled SQL generation assistant. "
        "Translate the following natural language question into a valid SQL query. "
        "Always include ProductId and Status in the SELECT clause if available. "
        "Generate ONLY the SQL query, no explanation.\n\n"
        "Available DataFrames:\n"
        "purchase_order_df(PONumber, ProductId, SupplierId, OrderDate, ExpectedDeliveryDate, ActualReciptDate, Status, TotalCost)\n"
        "inventory_stock_df(InventoryId, ProductId, WareHouseId, CurrentStock, ReorderPoint, SafetyStock, LastUpdated)\n\n"
        "User Question: {application}"
    )
    chain = prompt | getllm
    sql_query = chain.invoke({"application": state["application"]}).content
    # Clean markdown
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    print(f"Generated SQL Query:\n{sql_query}")

    # Deterministic, correct result with pandas
    result_df = build_tabular_output(inventory_stock_df, purchase_order_df)

    print("\nFinal Tabular Output:")
    if not result_df.empty:
        print(result_df.to_string(index=False))
    else:
        print("No products reached reorder point on the reference date.")

    # Return rows as structured data and keep SQL for transparency
    return {"sql_query": sql_query, "response": result_df.to_dict(orient="records")}


def categorize_query(state: State) -> State:
  print("\nCategorizing the input query from the user : ")
  prompt = ChatPromptTemplate.from_template(
      "categorize the input query based upon the followinig keywords 'Moniter' and 'forecaste' and return the keyword as application output"
      "Application : {application}"
  )
  chain = prompt | getllm
  input_keyword = chain.invoke({"application": state["application"]}).content
  print(f"Input keyword: {input_keyword}")
  return {"input_keyword" : input_keyword}

def monitot_agent(state: State) -> State:
  print("\nMoniter the report Successfully, Entered Here : ")
  summary_result = summary(state)
  return {
        "response": "we are successfully implemented the langgarph and called the Moniter.",
        "sql_query": summary_result["sql_query"]
    }

def forcaste_agent(state: State) -> State:
  print("\nForecast the report Successfully, Entered Here : ")
  return {"response" :"we are successfully implemented the langgarph and called the Forecaste."}

def summary_agent(state: State) -> State:
  print("Sending summary report")
  summary_result = summary(state)
  return {
        "response": "we are successfully implemented the langgarph and called the summary.",
        "sql_query": summary_result["sql_query"]
    }


workflow.add_node("categorize_query", categorize_query)
workflow.add_node("monitot_agent", monitot_agent)
workflow.add_node("forcaste_agent", forcaste_agent)
workflow.add_node("summary_agent", summary_agent)

def route_app(state: State) -> str:
    keyword = state["input_keyword"].lower()
    if "moniter" in keyword:
        return "monitot_agent"
    elif "forecaste" in keyword:
        return "forcaste_agent"
    else:
        return "summary_agent"
    
workflow.add_conditional_edges("categorize_query", route_app)
workflow.add_edge(START, "categorize_query")
workflow.add_edge("monitot_agent", END)
workflow.add_edge("forcaste_agent", END)
workflow.add_edge("summary_agent", END)

app = workflow.compile()
def run_candidate_screening(application: str):
    results = app.invoke({"application": application})
    return {
        "response": results.get("response"),
        "sql_query": results.get("sql_query")
    }

application_text = "Which product have reached reorder point today and orders are placed?"
results = run_candidate_screening(application_text)
print("\n\nComputed Results :")
print(f"Application: {application_text}")
print(f"Response: {results['response']}")
print(f"sql_query: {results['sql_query']}")
