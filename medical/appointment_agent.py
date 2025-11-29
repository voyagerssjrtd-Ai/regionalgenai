from azure_llm import getMassGpt
import json
from datetime import datetime, timedelta
import appointmentAgents.doctor_agent,appointmentAgents.lab_agent,appointmentAgents.disease_agent,appointmentAgents.service_agent,appointmentAgents.fallback_agent

llm = getMassGpt()

def appointment_book_agent(state):
    query = state["query"]

    # Ask LLM to extract structured entities
    raw_entities = llm.invoke({
        "prompt": f"""
        Extract entities from this appointment request as JSON.
        Keys: type (doctor/lab/disease/service), doctor_name, specialty, department,
              test, disease, service, date, time, location.
        Rules:
        - If no date is mentioned, set "date" to "tomorrow".
        - If no time is mentioned, set "time" to "09:00".
        Input: "{query}"
        """
    })

    try:
        entities = json.loads(raw_entities)
    except Exception:
        entities = {}

    # Handle date
    date_str = entities.get("date")
    if not date_str or date_str.lower() == "tomorrow":
        parsed_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except Exception:
            parsed_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Handle time
    time_str = entities.get("time") or "09:00"

    # Update state with extracted values
    state.update({
        "kind": entities.get("type"),
        "doctor_name": entities.get("doctor_name"),
        "specialty": entities.get("specialty"),
        "department": entities.get("department"),
        "test": entities.get("test"),
        "disease": entities.get("disease"),
        "service": entities.get("service"),
        "date": parsed_date,
        "time": time_str,
        "location": entities.get("location"),
        # Combine date and time into one string for DB queries
        "preferred_start": f"{parsed_date} {time_str}"
    })

   
    kind = state["kind"]
    # Route based on LLM intent
    if kind == "doctor":
        return doctor_agent(state)
    elif kind == "lab":
        return lab_agent(state)
    elif kind == "disease":
        return disease_agent(state)
    elif kind == "service":
        return service_agent(state)
    else:
        return fallback_agent(state)

    

    state["output"] = "Need to Implement"
    return state
