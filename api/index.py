from flask import Flask, jsonify, request
from datetime import datetime
import os
import sys

# Menambahkan root direktori ke path agar modul backend.database bisa di-import
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from backend import database

# Definisikan folder frontend secara dinamis
static_dir = os.path.join(ROOT_DIR, 'backend', 'frontend')

app = Flask(__name__, static_folder=static_dir, static_url_path='')

# In-memory store untuk status terkini (Vercel serverless bisa restart, tapi akan mengambil data terakhir dari database)
latest_reading = {
    'status_cuaca': 'Belum ada data',
    'kondisi_jemuran': 'Belum ada data',
    'warna': 'gray',
    'peringatan': 'Aman',
    'timestamp': '-'
}

# Pastikan database terbuat saat module di-import (terutama jika menggunakan SQLite lokal)
try:
    database.init_db()
except Exception as e:
    print(f"[!] Gagal menginisialisasi database saat start: {e}")

@app.route('/')
def index():
    """Menyajikan halaman utama dashboard."""
    return app.send_static_file('index.html')

@app.route('/api/update', methods=['POST'])
def update_weather():
    """Endpoint API untuk menerima pembaruan sensor."""
    global latest_reading
    
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
        
    status_cuaca = data.get('status_cuaca')
    kondisi_jemuran = data.get('kondisi_jemuran')
    warna = data.get('warna', 'gray')
    peringatan = data.get('peringatan', 'Aman')
    
    if not status_cuaca or not kondisi_jemuran:
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    latest_reading = {
        'status_cuaca': status_cuaca,
        'kondisi_jemuran': kondisi_jemuran,
        'warna': warna,
        'peringatan': peringatan,
        'timestamp': now_str
    }
    
    # Logika Cerdas: Simpan ke riwayat database jika ada perubahan
    try:
        last_log = database.get_latest_log()
        if not last_log or last_log['status_cuaca'] != status_cuaca or last_log['kondisi_jemuran'] != kondisi_jemuran:
            database.add_log(status_cuaca, kondisi_jemuran, warna, peringatan)
            logged = True
        else:
            logged = False
    except Exception as db_err:
        print(f"[-] Gagal menyimpan log database: {db_err}")
        logged = False
        
    return jsonify({
        'status': 'success',
        'message': 'Data updated successfully',
        'logged_to_history': logged,
        'data': latest_reading
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Mengambil status cuaca terkini."""
    global latest_reading
    
    # Fallback: Jika data memory kosong (karena serverless instance baru nyala), ambil data terakhir dari database
    if latest_reading['status_cuaca'] == 'Belum ada data':
        try:
            last_log = database.get_latest_log()
            if last_log:
                latest_reading = {
                    'status_cuaca': last_log['status_cuaca'],
                    'kondisi_jemuran': last_log['kondisi_jemuran'],
                    'warna': last_log['warna'],
                    'peringatan': last_log['peringatan'],
                    'timestamp': last_log['timestamp']
                }
        except Exception as db_err:
            print(f"[-] Gagal mengambil status database: {db_err}")
            
    return jsonify(latest_reading)

@app.route('/api/history', methods=['GET'])
def get_history():
    """Mengambil riwayat log perubahan."""
    try:
        history = database.get_history(limit=30)
    except Exception as db_err:
        print(f"[-] Gagal mengambil riwayat database: {db_err}")
        history = []
    return jsonify(history)

@app.route('/api/debug', methods=['GET'])
def debug_db():
    """Endpoint diagnostik untuk memeriksa koneksi database."""
    info = {}
    try:
        db_url = os.environ.get('DATABASE_URL')
        info['has_db_url'] = db_url is not None
        if db_url:
            # Sembunyikan password demi keamanan
            # Format umum: postgresql://username:password@host:port/database
            parts = db_url.split('@')
            if len(parts) > 1:
                prefix = parts[0].split(':')
                if len(prefix) > 2:
                    prefix[2] = '***'
                info['db_url_masked'] = ':'.join(prefix) + '@' + parts[1]
            else:
                info['db_url_masked'] = 'format URL tidak valid'
        
        # Uji koneksi
        conn, is_postgres = database.get_connection()
        info['is_postgres'] = is_postgres
        cursor = conn.cursor()
        
        # Jalankan test query
        cursor.execute("SELECT 1")
        cursor.fetchone()
        info['test_query_select_1'] = 'SUKSES'
        
        # Cek daftar tabel
        if is_postgres:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            
        tables = [r[0] for r in cursor.fetchall()]
        info['tables_found'] = tables
        
        # Cek jumlah data di tabel riwayat_jemuran
        if 'riwayat_jemuran' in tables:
            cursor.execute("SELECT COUNT(*) FROM riwayat_jemuran")
            info['total_rows_in_riwayat'] = cursor.fetchone()[0]
            
            # Cek data terakhir
            cursor.execute("SELECT * FROM riwayat_jemuran ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            info['latest_row'] = database.row_to_dict(cursor, row)
        else:
            info['total_rows_in_riwayat'] = 'Tabel riwayat_jemuran tidak ditemukan!'
            
        conn.close()
        info['connection_status'] = 'SUKSES CONNECT KE DATABASE'
    except Exception as e:
        info['connection_status'] = 'GAGAL'
        info['error_message'] = str(e)
        import traceback
        info['traceback'] = traceback.format_exc()
        
    return jsonify(info)

# Untuk dijalankan lokal menggunakan python api/index.py
if __name__ == '__main__':
    database.init_db()
    print("=== RUNNING LOCAL SERVER (VERCEL HANDLER) ===")
    app.run(host='0.0.0.0', port=5000, debug=True)
