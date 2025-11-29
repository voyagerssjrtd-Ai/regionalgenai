from workflow import app
import json

def calling_langgarph():

    user_input = input("Enter request: ")  # e.g., "forecast SKU001"

    result = app.invoke({
        "query": user_input
    })

    print("\n====== SMART INVENTORY AGENT OUTPUT ======")
    print(result["intent"])
    print(result["output"])
    print("==========================================\n")
    return result["output"]