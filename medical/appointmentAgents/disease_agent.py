def disease_agent(state: dict) -> dict:
    preferred, alternatives = find_matching_slots("disease", state["disease"], state["preferred_start"])
    if preferred and book_slot("disease", state["disease"], state["preferred_start"]):
        state["status"] = "confirmed"
        state["booked_slot"] = state["preferred_start"]
        state["output"] = f"Consultation for {state['disease']} with {state['specialty']} confirmed for {state['preferred_start']}."
    else:
        state["status"] = "unavailable"
        state["alternatives"] = suggest_alternatives_json(alternatives)
        state["output"] = f"Requested consultation slot unavailable. Alternatives provided."
    return state