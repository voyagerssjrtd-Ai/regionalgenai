from workflow import app
import json

def calling_langgarph():
    user_input = input("Enter request: ")

    result = app.invoke({
        "query": user_input
    })

    print("\n====== SMART INVENTORY AGENT OUTPUT ======")
    print(result["intent"])
    print(result["kind"])
    print(result["status"])
    if "alternatives" in result:
        print(result["alternatives"])
    print(result["output"])
    print("==========================================\n")
    return result["output"]