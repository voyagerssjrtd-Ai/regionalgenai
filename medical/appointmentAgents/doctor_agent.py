def doctor_agent(state: dict) -> dict:
    preferred, alternatives = find_matching_slots("doctor", state["doctor_name"], state["preferred_start"])
    if preferred and book_slot("doctor", state["doctor_name"], state["preferred_start"]):
        state["status"] = "confirmed"
        state["booked_slot"] = state["preferred_start"]
        state["output"] = f"Doctor appointment with {state['doctor_name']} confirmed for {state['preferred_start']}."
    else:
        state["status"] = "unavailable"
        state["alternatives"] = suggest_alternatives_json(alternatives)
        state["output"] = f"Requested slot unavailable. Alternatives provided."
    return state