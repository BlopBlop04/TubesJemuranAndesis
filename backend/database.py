import os
from datetime import datetime

# Load .env file jika dijalankan lokal
try:
    from dotenv import load_dotenv
    # Cari file .env di folder sistem-monitoring-jemuran/
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
except ImportError:
    pass

def get_connection():
    """
    Membuat koneksi ke database.
    Mengembalikan tuple (conn, is_postgres).
    Jika env DATABASE_URL tersedia, menggunakan PostgreSQL (Supabase).
    Jika tidak, fallback ke SQLite lokal.
    """
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url:
        import psycopg2
        # Vercel / Heroku terkadang memberikan postgres://, ubah ke postgresql:// untuk psycopg2
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
        conn = psycopg2.connect(db_url)
        return conn, True
    else:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jemuran.db')
        conn = sqlite3.connect(db_path)
        return conn, False

def row_to_dict(cursor, row):
    """Mengubah hasil query baris (tuple) menjadi dictionary berdasarkan nama kolom."""
    if row is None:
        return None
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def init_db():
    """Menginisialisasi tabel database (PostgreSQL atau SQLite)."""
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    if is_postgres:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS riwayat_jemuran (
                id SERIAL PRIMARY KEY,
                timestamp VARCHAR(50) NOT NULL,
                status_cuaca VARCHAR(50) NOT NULL,
                kondisi_jemuran VARCHAR(100) NOT NULL,
                warna VARCHAR(20) NOT NULL,
                peringatan VARCHAR(200) NOT NULL
            )
        ''')
    else:
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
    """Menambahkan log cuaca baru."""
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if is_postgres:
        query = '''
            INSERT INTO riwayat_jemuran (timestamp, status_cuaca, kondisi_jemuran, warna, peringatan)
            VALUES (%s, %s, %s, %s, %s)
        '''
    else:
        query = '''
            INSERT INTO riwayat_jemuran (timestamp, status_cuaca, kondisi_jemuran, warna, peringatan)
            VALUES (?, ?, ?, ?, ?)
        '''
        
    cursor.execute(query, (now_str, status_cuaca, kondisi_jemuran, warna, peringatan))
    conn.commit()
    conn.close()

def get_latest_log():
    """Mengambil log cuaca paling terakhir."""
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM riwayat_jemuran ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    
    result = row_to_dict(cursor, row)
    
    conn.close()
    return result

def get_history(limit=50):
    """Mengambil daftar riwayat perubahan cuaca."""
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    if is_postgres:
        query = 'SELECT * FROM riwayat_jemuran ORDER BY id DESC LIMIT %s'
    else:
        query = 'SELECT * FROM riwayat_jemuran ORDER BY id DESC LIMIT ?'
        
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    
    results = [row_to_dict(cursor, row) for row in rows]
    
    conn.close()
    return results
