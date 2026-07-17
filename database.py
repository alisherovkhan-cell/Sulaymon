import sqlite3

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    # Foydalanuvchilar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referred_by INTEGER,
            stars_balance INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, referrer_id=None):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    
    # Foydalanuvchi bor yoki yo'qligini tekshirish
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        # Yangi foydalanuvchini qo'shish
        cursor.execute("INSERT INTO users (user_id, referred_by, stars_balance) VALUES (?, ?, ?)", (user_id, referrer_id, 0))
        
        # Agar taklif qilgan odam bo'lsa, unga Stars (ball) qo'shish
        if referrer_id:
            cursor.execute("UPDATE users SET stars_balance = stars_balance + 5 WHERE user_id = ?", (referrer_id,))
            conn.commit()
            conn.close()
            return True  # Yangi referal muvaffaqiyatli qo'shildi
            
    conn.commit()
    conn.close()
    return False

def get_user_stars(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT stars_balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0
  
