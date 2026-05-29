import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jemuran.db')

def init_db():
    """Menginisialisasi database SQLite dan membuat tabel jika belum ada."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS riwayat_jemuran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            status_cuaca TEXT NOT NULL,
            kondisi_jemuran TEXT NOT NULL,
            warna TEXT NOT NULL,
            peringatan TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_log(status_cuaca, kondisi_jemuran, warna, peringatan):
    """Menambahkan log cuaca baru ke database dengan timestamp saat ini."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Simpan timestamp dalam format lokal (misal YYYY-MM-DD HH:MM:SS)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO riwayat_jemuran (timestamp, status_cuaca, kondisi_jemuran, warna, peringatan)
        VALUES (?, ?, ?, ?, ?)
    ''', (now_str, status_cuaca, kondisi_jemuran, warna, peringatan))
    
    conn.commit()
    conn.close()

def get_latest_log():
    """Mengambil log cuaca paling terakhir."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM riwayat_jemuran ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_history(limit=50):
    """Mengambil riwayat log cuaca dengan batas tertentu (default 50 data terakhir)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM riwayat_jemuran ORDER BY id DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    
    conn.close()
    return [dict(row) for row in rows]
