from app.db.connection import db

def log_event(user_id:int,event:str)->None:
    with db() as conn:
        exists=conn.execute("SELECT COUNT(*) FROM analytics WHERE user_id=? AND event=?",(user_id,event)).fetchone()[0]
        if exists==0:
            conn.execute("INSERT INTO analytics(user_id,event) VALUES(?,?)",(user_id,event))

def has_event(user_id:int,event:str)->bool:
    with db() as conn:
        return conn.execute("SELECT COUNT(*) FROM analytics WHERE user_id=? AND event=?",(user_id,event)).fetchone()[0]>0
