import sqlite3

def init_db():
    conn = sqlite3.connect('kyc.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS kyc_info (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        dob TEXT,
        id_number TEXT,
        file_path TEXT,
        status TEXT,
        attempts INTEGER DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

def store_kyc_info(user_id, name, dob, id_number, file_path):
    conn = sqlite3.connect('kyc.db')
    c = conn.cursor()
    c.execute('''
    INSERT OR REPLACE INTO kyc_info (user_id, name, dob, id_number, file_path, status, attempts)
    VALUES (?, ?, ?, ?, ?, 'Pending', COALESCE((SELECT attempts FROM kyc_info WHERE user_id = ?), 0))
    ''', (user_id, name, dob, id_number, file_path, user_id))
    conn.commit()
    conn.close()

def get_kyc_status(user_id):
    conn = sqlite3.connect('kyc.db')
    c = conn.cursor()
    c.execute('SELECT status FROM kyc_info WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_kyc_info(user_id):
    conn = sqlite3.connect('kyc.db')
    c = conn.cursor()
    c.execute('SELECT * FROM kyc_info WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def get_attempts(user_id):
    conn = sqlite3.connect('kyc.db')
    c = conn.cursor()
    c.execute('SELECT attempts FROM kyc_info WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def approve_kyc(user_id):
    conn = sqlite3.connect('kyc.db')
    c = conn.cursor()
    c.execute('UPDATE kyc_info SET status = "Approved" WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def reject_kyc(user_id):
    conn = sqlite3.connect('kyc.db')
    c = conn.cursor()
    c.execute('UPDATE kyc_info SET status = "Rejected" WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def update_kyc_status(user_id, status):
    conn = sqlite3.connect('kyc.db')
    c = conn.cursor()
    c.execute('UPDATE kyc_info SET status = ? WHERE user_id = ?', (status, user_id))
    conn.commit()
    conn.close()

def reset_kyc(user_id):
    conn = sqlite3.connect('kyc.db')
    c = conn.cursor()
    c.execute('DELETE FROM kyc_info WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_all_kycs():
    conn = sqlite3.connect('kyc.db')
    c = conn.cursor()
    c.execute('SELECT * FROM kyc_info')
    results = c.fetchall()
    conn.close()
    return results

init_db()
