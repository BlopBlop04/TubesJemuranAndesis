from flask import Flask, jsonify, request, send_from_directory
import database
from datetime import datetime
import os

app = Flask(__name__, static_folder='frontend', static_url_path='')

# In-memory store untuk data terbaru (agar update real-time 1 detik sekali tetap tampil di web)
latest_reading = {
    'status_cuaca': 'Belum ada data',
    'kondisi_jemuran': 'Belum ada data',
    'warna': 'gray',
    'peringatan': 'Aman',
    'timestamp': '-'
}

@app.route('/')
def index():
    """Menyajikan halaman utama dashboard."""
    return app.send_static_file('index.html')

@app.route('/api/update', methods=['POST'])
def update_weather():
    """
    Endpoint untuk menerima data dari script transmitter (pyserial).
    Mendukung JSON dan Form Data.
    """
    global latest_reading
    
    # Ambil data dari JSON atau Form
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
    
    # Update data terbaru di memori
    latest_reading = {
        'status_cuaca': status_cuaca,
        'kondisi_jemuran': kondisi_jemuran,
        'warna': warna,
        'peringatan': peringatan,
        'timestamp': now_str
    }
    
    # Logika Cerdas: Simpan ke riwayat hanya jika ada perubahan status cuaca ATAU kondisi jemuran
    # Hal ini dilakukan untuk menghemat penyimpanan database SQLite agar tidak mencatat data yang sama setiap detik
    last_log = database.get_latest_log()
    if not last_log or last_log['status_cuaca'] != status_cuaca or last_log['kondisi_jemuran'] != kondisi_jemuran:
        database.add_log(status_cuaca, kondisi_jemuran, warna, peringatan)
        logged = True
    else:
        logged = False
        
    return jsonify({
        'status': 'success',
        'message': 'Data updated successfully',
        'logged_to_history': logged,
        'data': latest_reading
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Mengambil status cuaca dan kondisi jemuran terkini."""
    global latest_reading
    
    # Jika belum ada data masuk ke memory, coba ambil data terakhir dari database
    if latest_reading['status_cuaca'] == 'Belum ada data':
        last_log = database.get_latest_log()
        if last_log:
            latest_reading = {
                'status_cuaca': last_log['status_cuaca'],
                'kondisi_jemuran': last_log['kondisi_jemuran'],
                'warna': last_log['warna'],
                'peringatan': last_log['peringatan'],
                'timestamp': last_log['timestamp']
            }
            
    return jsonify(latest_reading)

@app.route('/api/history', methods=['GET'])
def get_history():
    """Mengambil daftar riwayat perubahan kondisi cuaca."""
    history = database.get_history(limit=30) # Batasi 30 log terakhir agar tabel tetap rapi
    return jsonify(history)

if __name__ == '__main__':
    # Inisialisasi database
    database.init_db()
    
    print("=== SERVER JEMURAN AKTIF ===")
    print("Membuka server di: http://127.0.0.1:5000")
    print("=============================")
    app.run(host='0.0.0.0', port=5000, debug=True)
