from app.db.connection import db

def init_db() -> None:
    with db() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, current_lesson INTEGER DEFAULT 0, stage TEXT DEFAULT 'start', funnel_started INTEGER DEFAULT 0, segment TEXT DEFAULT 'cold', access_deadline TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS analytics (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, event TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS crm_leads (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, name TEXT, phone TEXT, interest TEXT, budget TEXT, status TEXT DEFAULT 'new', pain TEXT, next_action TEXT, next_action_at TEXT, manager_note TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS wb_unit_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, api_key TEXT, nm_id TEXT, vendor_code TEXT, product_name TEXT, work_model TEXT, warehouse_name TEXT, purchase_price REAL, fulfilment_price REAL, tax_percent REAL, other_expenses REAL, salary_expenses REAL, price REAL, spp_percent REAL, price_with_spp REAL, buyout_percent REAL, ads_percent REAL, ads_rub REAL, commission_percent REAL, commission_rub REAL, logistics_rub REAL, reverse_logistics_rub REAL, storage_rub REAL, acceptance_rub REAL, transit_rub REAL, width REAL, height REAL, length REAL, weight REAL, profit_per_unit REAL, margin_percent REAL, roi_percent REAL, stage TEXT DEFAULT 'api_key', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS products_cache (user_id INTEGER PRIMARY KEY, payload TEXT NOT NULL, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS scheduled_tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, task_type TEXT NOT NULL, run_at TEXT NOT NULL, payload TEXT, status TEXT DEFAULT 'pending', last_error TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_due ON scheduled_tasks(status, run_at)")
