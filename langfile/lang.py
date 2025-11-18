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
        def insecure_request(*args, _original=original, **kwargs):
            kwargs["verify"] = False
            return _original(*args, **kwargs)
        setattr(requests, method, insecure_request)

def getllm(query):
    client = httpx.Client(verify=False)
    llm = ChatOpenAI(
        base_url="https://genailab.tcs.in",
        model="azure/genailab-maas-gpt-4o",
        api_key="sk-K5cCB7yk7rc3ex2NV3-TWw",
        http_client=client
    )
    return llm.invoke(query)

class State(TypedDict):
    application: str
    input_keyword: str
    sql_query: str
    response: str

workflow = StateGraph(State)

# --- Helpers ---
def normalize_dates(purchase_order_df: pd.DataFrame, inventory_stock_df: pd.DataFrame):
    for col in ["OrderDate", "ExpectedDeliveryDate", "ActualReciptDate"]:
        purchase_order_df[col] = pd.to_datetime(purchase_order_df[col], dayfirst=True, errors="coerce")
    inventory_stock_df["LastUpdated"] = pd.to_datetime(inventory_stock_df["LastUpdated"], dayfirst=True, errors="coerce")
    return purchase_order_df, inventory_stock_df

def build_tabular_output(inventory_stock_df: pd.DataFrame, purchase_order_df: pd.DataFrame):
    ref_date = inventory_stock_df["LastUpdated"].max().date()
    reached = inventory_stock_df[
        (inventory_stock_df["CurrentStock"] <= inventory_stock_df["ReorderPoint"]) &
        (inventory_stock_df["LastUpdated"].dt.date == ref_date)
    ][["ProductId", "CurrentStock", "ReorderPoint", "LastUpdated"]].copy()

    orders_today = purchase_order_df[
        purchase_order_df["OrderDate"].dt.date == ref_date
    ][["ProductId", "Status"]].copy()

    result = reached.merge(orders_today, on="ProductId", how="left")

    def comment_row(row):
        if pd.notna(row["Status"]) and row["Status"] == "ORDER_PLACED":
            return "Order placed successfully"
        return f"No order placed - stock {row['CurrentStock']} <= reorder {row['ReorderPoint']} on {row['LastUpdated'].date()}"

    result["Comment"] = result.apply(comment_row, axis=1)
    return result[["ProductId", "Status", "Comment"]]

# --- Summary ---
def summary(state: State) -> State:
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

    purchase_order_df, inventory_stock_df = normalize_dates(purchase_order_df, inventory_stock_df)
    result_df = build_tabular_output(inventory_stock_df, purchase_order_df)

    return {"response": result_df.to_dict(orient="records")}

def summary_agent(state: State) -> State:
    summary_result = summary(state)
    return {"response": summary_result["response"]}

workflow.add_node("summary_agent", summary_agent)
workflow.add_edge(START, "summary_agent")
workflow.add_edge("summary_agent", END)

app = workflow.compile()

def run_candidate_screening(application: str):
    results = app.invoke({"application": application})
    return results.get("response")

application_text = "Which product have reached reorder point today and orders are placed?"
results = run_candidate_screening(application_text)

# --- Final Output Only ---
df = pd.DataFrame(results)
print(df.to_string(index=False))
