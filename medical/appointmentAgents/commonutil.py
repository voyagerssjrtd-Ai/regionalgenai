import sqlite3, json

def find_matching_slots(resource_type, resource_id, preferred_start):
    conn = sqlite3.connect("triage.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Check if preferred slot exists
    c.execute("""
        SELECT * FROM availability
        WHERE resource_type=? AND resource_id=? AND slot_start=?
    """, (resource_type, resource_id, preferred_start))
    preferred = c.fetchone()

    # Get up to 5 alternative slots
    c.execute("""
        SELECT * FROM availability
        WHERE resource_type=? AND resource_id=? AND is_available=1
        ORDER BY slot_start ASC
        LIMIT 5
    """, (resource_type, resource_id))
    alternatives = c.fetchall()

    conn.close()
    return preferred, alternatives

def suggest_alternatives_json(alts):
    return json.dumps([dict(r) for r in alts], indent=2)

def book_slot(resource_type, resource_id, slot_start):
    conn = sqlite3.connect("triage.db")
    c = conn.cursor()
    c.execute("""
        UPDATE availability
        SET is_available=0
        WHERE resource_type=? AND resource_id=? AND slot_start=? AND is_available=1
    """, (resource_type, resource_id, slot_start))
    ok = (c.rowcount == 1)
    conn.commit()
    conn.close()
    return ok