# from azure_llm import getMassGpt
# from langchain_core.messages import HumanMessage
# import json
# from datetime import datetime, timedelta
# from doctor_agent import doctor_appoint_agent
# from lab_agent import lab_appoint_agent
# from disease_agent import disease_appoint_agent
# from service_agent import service_appoint_agent
# from fallback_agent import fallback_appoint_agent

# llm = getMassGpt()

# def appointment_book_agent(state):
#     query = state["query"]
#     print("Entered Appointment Booking")

#     raw_entities = llm.invoke([
#         HumanMessage(content=f"""
#         Extract entities from this appointment request as JSON.
#         Keys: type (doctor/lab/disease/service), doctor_name, specialty, department,
#             test, disease, service, date, time, location.
#         Rules:
#         - If no date is mentioned, set "date" to "tomorrow".
#         - If no time is mentioned, set "time" to "09:00".
#         Input: "{query}"
#         """)
#     ])

#     try:
#         entities = json.loads(raw_entities)
#     except Exception:
#         entities = {}

#     # Handle date
#     date_str = entities.get("date")
#     if not date_str or date_str.lower() == "tomorrow":
#         parsed_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
#     else:
#         try:
#             parsed_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
#         except Exception:
#             parsed_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

#     # Handle time
#     time_str = entities.get("time") or "09:00"

#     # Update state with extracted values
#     state.update({
#         "kind": entities.get("type"),
#         "doctor_name": entities.get("doctor_name"),
#         "specialty": entities.get("specialty"),
#         "department": entities.get("department"),
#         "test": entities.get("test"),
#         "disease": entities.get("disease"),
#         "service": entities.get("service"),
#         "date": parsed_date,
#         "time": time_str,
#         "location": entities.get("location"),
#         # Combine date and time into one string for DB queries
#         "preferred_start": f"{parsed_date} {time_str}"
#     })

#     print("Came Here")
#     print(state["kind"])
   
#     kind = state["kind"]
#     # Route based on LLM intent
#     if kind == "doctor":
#         return doctor_appoint_agent(state)
#     elif kind == "lab":
#         return lab_appoint_agent(state)
#     elif kind == "disease":
#         return doctor_appoint_agent(state)
#     elif kind == "service":
#         return service_appoint_agent(state)
#     else:
#         return fallback_appoint_agent(state)

# from azure_llm import getMassGpt
# from langchain_core.messages import HumanMessage
# import json
# import re
# from datetime import datetime, timedelta
# from doctor_agent import doctor_appoint_agent
# from lab_agent import lab_appoint_agent
# from disease_agent import disease_appoint_agent
# from service_agent import service_appoint_agent
# from fallback_agent import fallback_appoint_agent
# from azure_llm import getMassGpt

# llm = getMassGpt()
# def appointment_book_agent(state):
#     query = state["query"]
#     print("Entered Appointment Booking")

#     raw_entities_msg = llm.invoke([
#         HumanMessage(content=f"""
#         Extract entities from this appointment request.
#         Return ONLY valid JSON, no extra text, no explanations.
#         Keys: type (doctor/lab/disease/service), doctor_name, specialty, department,
#             test, disease, service, date, time, location.
#         Rules:
#         - If no date is mentioned, set "date" to "tomorrow".
#         - If no time is mentioned, set "time" to "09:00".
#         Input: "{query}"
#         """)
#     ])
#     raw_text = raw_entities_msg.content.strip()
#     match = re.search(r"\{.*\}", raw_text, re.DOTALL)
#     if match:
#         raw_text = match.group(0)

#     try:
#         # ✅ Use .content to get the text
#         entities = json.loads(raw_text)
#     except Exception:
#         print("Failed to parse JSON from LLM output:", raw_text)
#         entities = {}

#     # Handle date
#     date_str = entities.get("date")
#     if not date_str or date_str.lower() == "tomorrow":
#         parsed_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
#     else:
#         try:
#             parsed_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
#         except Exception:
#             parsed_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

#     # Handle time
#     time_str = entities.get("time") or "09:00"

#     # Update state with extracted values
#     state.update({
#         "kind": entities.get("type"),
#         "doctor_name": entities.get("doctor_name"),
#         "specialty": entities.get("specialty"),
#         "department": entities.get("department"),
#         "test": entities.get("test"),
#         "disease": entities.get("disease"),
#         "service": entities.get("service"),
#         "date": parsed_date,
#         "time": time_str,
#         "location": entities.get("location"),
#         "preferred_start": f"{parsed_date} {time_str}"
#     })

#     print("Came Here")
#     print(state["kind"])
   
#     kind = state["kind"]
#     if kind == "doctor":
#         return doctor_appoint_agent(state)
#     elif kind == "lab":
#         return lab_appoint_agent(state)
#     elif kind == "disease":
#         return doctor_appoint_agent(state)
#     elif kind == "service":
#         return service_appoint_agent(state)
#     else:
#         return fallback_appoint_agent(state)

import json
import re
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage
from azure_llm import getMassGpt

from doctor_agent import doctor_appoint_agent
from lab_agent import lab_appoint_agent
from disease_agent import disease_appoint_agent
from service_agent import service_appoint_agent
from fallback_agent import fallback_appoint_agent

llm = getMassGpt()

# --- Helpers ---

def extract_entities(query: str) -> dict:
    """Call LLM to extract structured entities from the query."""
    raw_entities_msg = llm.invoke([
        HumanMessage(content=f"""
        Extract entities from this appointment request.
        Return ONLY valid JSON, no extra text, no explanations.
        Keys: type (doctor/lab/disease/service), doctor_name, specialty, department,
              test, disease, service, date, time, location.
        Rules:
        - If no date is mentioned, set "date" to "tomorrow".
        - If no time is mentioned, set "time" to "09:00".
        Input: "{query}"
        """)
    ])
    raw_text = raw_entities_msg.content.strip()
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        raw_text = match.group(0)

    try:
        return json.loads(raw_text)
    except Exception:
        print("Failed to parse JSON from LLM output:", raw_text)
        return {}

def normalize_date(date_str: str) -> str:
    """Normalize date string to YYYY-MM-DD, default to tomorrow."""
    if not date_str or date_str.lower() == "tomorrow":
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

def normalize_time(time_str: str) -> str:
    """Normalize time string, default to 09:00."""
    return time_str or "09:00"

# --- Main Agent ---

def appointment_book_agent(state: dict):
    query = state.get("query", "")
    print("Entered Appointment Booking")

    entities = extract_entities(query)

    parsed_date = normalize_date(entities.get("date"))
    time_str = normalize_time(entities.get("time"))

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
        "preferred_start": f"{parsed_date} {time_str}"
    })

    print("Routing based on kind:", state["kind"])

    # Routing map
    agent_map = {
        "doctor": doctor_appoint_agent,
        "lab": lab_appoint_agent,
        "disease": doctor_appoint_agent,  # disease handled by doctor agent
        "service": service_appoint_agent,
    }

    agent = agent_map.get(state["kind"], fallback_appoint_agent)
    return agent(state)
