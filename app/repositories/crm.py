from app.db.connection import db

def upsert_lead(user_id:int, username:str|None=None, **kwargs)->None:
    with db() as conn:
        existing=conn.execute("SELECT id FROM crm_leads WHERE user_id=?",(user_id,)).fetchone()
        if not existing:
            conn.execute("INSERT INTO crm_leads(user_id,username) VALUES(?,?)",(user_id,username))
        if kwargs:
            fields=", ".join(f"{k}=?" for k in kwargs)
            values=list(kwargs.values())+[user_id]
            conn.execute(f"UPDATE crm_leads SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",values)

def find_lead(data:dict)->int|None:
    with db() as conn:
        user_id=data.get("user_id"); username=data.get("username"); name=data.get("name"); phone=data.get("phone")
        lead=None
        if user_id: lead=conn.execute("SELECT user_id FROM crm_leads WHERE user_id=?",(int(user_id),)).fetchone()
        if not lead and username: lead=conn.execute("SELECT user_id FROM crm_leads WHERE username=?",(str(username).replace('@',''),)).fetchone()
        if not lead and phone: lead=conn.execute("SELECT user_id FROM crm_leads WHERE phone=?",(phone,)).fetchone()
        if not lead and name: lead=conn.execute("SELECT user_id FROM crm_leads WHERE name LIKE ?",(f"%{name}%",)).fetchone()
        return lead["user_id"] if lead else None

def update_lead_smart(user_id:int,data:dict)->None:
    allowed=["username","name","phone","interest","budget","status","pain","next_action","next_action_at","manager_note"]
    updates={f:data[f] for f in allowed if data.get(f) not in (None,"")}
    if updates: upsert_lead(user_id,data.get("username"),**updates)

def list_leads_by_status(status:str|None=None, callback_only:bool=False, limit:int=10):
    with db() as conn:
        if callback_only:
            return conn.execute("SELECT user_id,username,status,interest,budget,next_action_at FROM crm_leads WHERE next_action_at IS NOT NULL ORDER BY next_action_at ASC LIMIT ?",(limit,)).fetchall()
        return conn.execute("SELECT user_id,username,status,interest,budget,next_action_at FROM crm_leads WHERE status=? ORDER BY updated_at DESC LIMIT ?",(status,limit)).fetchall()

def get_lead(user_id:int):
    with db() as conn:
        return conn.execute("SELECT user_id, username, name, phone, interest, budget, status, pain, next_action, next_action_at, manager_note, created_at, updated_at FROM crm_leads WHERE user_id=?",(user_id,)).fetchone()

def all_leads():
    with db() as conn:
        return conn.execute("SELECT user_id, username, name, phone, interest, budget, status, pain, next_action, next_action_at, manager_note, created_at, updated_at FROM crm_leads").fetchall()
