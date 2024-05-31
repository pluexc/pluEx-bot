import sqlite3
import os

# Ensure the database directory exists
os.makedirs('db', exist_ok=True)

DB_PATH = 'db/plubot.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT,
            password TEXT,
            balance REAL DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS kyc_info (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            dob TEXT,
            id_number TEXT,
            file_path TEXT,
            status TEXT,
            attempts INTEGER,
            edited INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def create_user(user_id, email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    if c.fetchone():
        conn.close()
        return False
    c.execute('INSERT INTO users (user_id, email, password) VALUES (?, ?, ?)', (user_id, email, password))
    conn.commit()
    conn.close()
    return True

def is_user_registered(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return bool(user)

def update_user_balance(user_id, amount, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = c.fetchone()[0]
    if status == 'Successful':
        new_balance = balance + amount
    else:
        new_balance = balance
    c.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = c.fetchone()[0]
    conn.close()
    return balance

def delete_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM kyc_info WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# Initialize the database
init_db()
