from guardrails import validate_input_with_llm, route_query_with_llm

def route_query(state):
    print("----> Entered Route Query")
    validate_input_with_llm(state)
    state["intent"] = route_query_with_llm(state)
    print(state["intent"])
    return state