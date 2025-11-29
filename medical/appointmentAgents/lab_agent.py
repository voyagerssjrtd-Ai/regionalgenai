def lab_agent(state: dict) -> dict:
    preferred, alternatives = find_matching_slots("lab", state["test"], state["preferred_start"])
    if preferred and book_slot("lab", state["test"], state["preferred_start"]):
        state["status"] = "confirmed"
        state["booked_slot"] = state["preferred_start"]
        state["output"] = f"Lab test '{state['test']}' booked for {state['preferred_start']} at {state.get('location','default lab')}."
    else:
        state["status"] = "unavailable"
        state["alternatives"] = suggest_alternatives_json(alternatives)
        state["output"] = f"Requested lab slot unavailable. Alternatives provided."
    return state