import re
import sqlite3
import json
from datetime import datetime

def store_chatbot_response(llm_text):
    conn = sqlite3.connect("triage.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS triage_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        triage_level TEXT,
        reasoning TEXT,
        urgent_evaluation_needed TEXT,
        patient_actions TEXT,
        clinician_tasks TEXT,
        disclaimer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --- Parse function ---
    def parse_llm_output(text: str) -> dict:
        fields = {}
        for line in text.splitlines():
            match = re.match(r"-\s*\*\*(.+?)\*\*\s*:? (.*)", line.strip())
            if match:
                key, value = match.groups()
                key = key.lower().replace(" ", "_")
                fields[key] = value.strip()
        return fields

    parsed = parse_llm_output(llm_text)

    # --- Insert or Update ---
    def save_response(response: dict, update_latest=False):
        if update_latest:
            cursor.execute("""
            UPDATE triage_responses
            SET triage_level=?, reasoning=?, urgent_evaluation_needed=?, 
                patient_actions=?, clinician_tasks=?, disclaimer=?, created_at=?
            WHERE user_id=?
            """, (
                response.get("triage_level"),
                response.get("reasoning"),
                response.get("urgent_evaluation_needed"),
                response.get("patient_actions"),
                response.get("clinician_tasks"),
                response.get("disclaimer"),
                datetime.now(),
                response.get("id")
            ))
        else:
            cursor.execute("""
            INSERT INTO triage_responses 
            (user_id, triage_level, reasoning, urgent_evaluation_needed, patient_actions, clinician_tasks, disclaimer)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                response.get("id"),
                response.get("triage_level"),
                response.get("reasoning"),
                response.get("urgent_evaluation_needed"),
                response.get("patient_actions"),
                response.get("clinician_tasks"),
                response.get("disclaimer")
            ))
        conn.commit()

    # --- Save parsed response ---
    save_response(parsed, update_latest=False)  # append mode

    # Close connection
    conn.close()

"""
OUTPUT :
(1, '12345', 'Emergency', 'The patient has a history of hypertension and diabetes, and now presents with sudden chest pain and shortness of breath. These are high‑risk symptoms for acute cardiac events, requiring immediate attention.', 'Yes; ECG, cardiac enzymes, and continuous monitoring are necessary.', 'Seek emergency medical care immediately.', 'Perform ECG, order cardiac enzyme tests, monitor vital signs, and prepare for possible advanced cardiac intervention.', 'This information is based on the provided context and past records. It is not a substitute for professional medical advice. Patients should consult a licensed healthcare provider for diagnosis and treatment.', '2025-11-29 05:01:21')
(2, '67891', 'Emergency', 'The patient has a history of hypertension and diabetes, and now presents with sudden chest pain and shortness of breath. These are high‑risk symptoms for acute cardiac events, requiring immediate attention.', 'Yes; ECG, cardiac enzymes, and continuous monitoring are necessary.', 'Seek emergency medical care immediately.', 'Perform ECG, order cardiac enzyme tests, monitor vital signs, and prepare for possible advanced cardiac intervention.', 'This information is based on the provided context and past records. It is not a substitute for professional medical advice. Patients should consult a licensed healthcare provider for diagnosis and treatment.', '2025-11-29 05:04:47')
"""
def fetch_all_triage_responses():
    conn = sqlite3.connect("triage.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM triage_responses")
    rows = cursor.fetchall()
    conn.close()
    return rows


"""
OUTPUT:
User ID: 12345
Triage Level: Emergency
"""
def getRequiredColByUserId(userId,reqCol):
    conn = sqlite3.connect("triage.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM triage_responses WHERE user_id = ?", (userId,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    # Wrap the requested column in a dict and convert to JSON
    col_dict = {reqCol: row[reqCol]}
    return json.dumps(col_dict, indent=4)


"""
output:
(1, '12345', 'Emergency', 'The patient has a history of hypertension and diabetes, and now presents with sudden chest pain and shortness of breath. These are high‑risk symptoms for acute cardiac events, requiring immediate attention.', 'Yes; ECG, cardiac enzymes, and continuous monitoring are necessary.', 'Seek emergency medical care immediately.', 'Perform ECG, order cardiac enzyme tests, monitor vital signs, and prepare for possible advanced cardiac intervention.', 'This information is based on the provided context and past records. It is not a substitute for professional medical advice. Patients should consult a licensed healthcare provider for diagnosis and treatment.', '2025-11-29 05:01:21')
"""
def fetch_by_userId(userId):
    conn = sqlite3.connect("triage.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM triage_responses WHERE user_id = ?", (userId,))
    row = cursor.fetchone()
    record_dict = {col: row[col] for col in row.keys()}
    # Convert dictionary to JSON string
    record_json = json.dumps(record_dict, indent=4)
    conn.close()
    return record_json
