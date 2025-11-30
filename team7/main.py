from fastapi import FastAPI, File, UploadFile
from typing import List
from run import calling_langgarph
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

DB_FILE = "triage.db"
app = FastAPI()

@app.get("/")
def greet(): 
    return "Hello world"

@app.post("/saveFiles")
async def uploadDocuments(file: UploadFile = File(...)):
    file_ext = file.filename.split(".")[-1].lower()
    temp_path = f"temp_{file.filename.replace(' ', '_')}"
    with open(f'savedFiles/{file.filename}', "wb") as f:
        f.write(file.file.read())
    return "Successully Saved the file"

@app.post("/saveMultipleFiles")
async def uploadDocuments(files: List[UploadFile] = File(...)):
    for file in files :
        with open(f'savedFiles/{file.filename}', "wb") as f:
            f.write(file.file.read())
    return "Successully Saved all files"

@app.get("/userInput/{inputQuestion}")
def userInputQuestion(inputQuestion):
    return calling_langgarph(inputQuestion)

# --- Pydantic Models ---
class Doctor(BaseModel):
    name: str
    specialty: str
    department: str
    location: str

class Lab(BaseModel):
    name: str
    location: str

class Availability(BaseModel):
    resource_type: str   # "doctor" or "lab"
    resource_id: int
    slot_start: str      # YYYY-MM-DD HH:MM
    slot_end: str        # YYYY-MM-DD HH:MM
    is_available: int    # 0 or 1

class Appointment(BaseModel):
    user_id: str
    kind: str
    resource_id: int | None = None
    resource_type: str | None = None
    requested_slot: str | None = None
    booked_slot: str | None = None
    status: str
    suggested_alternatives: str | None = None

# --- Utility ---
def run_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(query, params)
        if fetch:
            return [dict(r) for r in c.fetchall()]
        conn.commit()
        return {"rows_affected": c.rowcount}

# --- Endpoints ---

# Doctors
@app.post("/doctors")
def create_doctor(doctor: Doctor):
    run_query(
        "INSERT INTO doctors (name, specialty, department, location) VALUES (?, ?, ?, ?)",
        (doctor.name, doctor.specialty, doctor.department, doctor.location),
    )
    return {"status": "success", "doctor": doctor}

@app.get("/doctors")
def get_doctors():
    return run_query("SELECT * FROM doctors", fetch=True)

# Labs
@app.post("/labs")
def create_lab(lab: Lab):
    run_query(
        "INSERT INTO labs (name, location) VALUES (?, ?)",
        (lab.name, lab.location),
    )
    return {"status": "success", "lab": lab}

@app.get("/labs")
def get_labs():
    return run_query("SELECT * FROM labs", fetch=True)

# Availability
@app.post("/availability")
def create_availability(av: Availability):
    run_query(
        "INSERT INTO availability (resource_type, resource_id, slot_start, slot_end, is_available) VALUES (?, ?, ?, ?, ?)",
        (av.resource_type, av.resource_id, av.slot_start, av.slot_end, av.is_available),
    )
    return {"status": "success", "availability": av}

@app.get("/availability")
def get_availability():
    return run_query("SELECT * FROM availability", fetch=True)

# Appointments
@app.post("/appointments")
def create_appointment(appt: Appointment):
    run_query(
        """INSERT INTO appointments 
           (user_id, kind, resource_id, resource_type, requested_slot, booked_slot, status, suggested_alternatives) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            appt.user_id,
            appt.kind,
            appt.resource_id,
            appt.resource_type,
            appt.requested_slot,
            appt.booked_slot,
            appt.status,
            appt.suggested_alternatives,
        ),
    )
    return {"status": "success", "appointment": appt}

@app.get("/appointments")
def get_appointments():
    return run_query("SELECT * FROM appointments", fetch=True)


